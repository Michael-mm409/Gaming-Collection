
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.order import Game, Category, Peripheral, Platform
from app.core.database import db
import csv
from io import TextIOWrapper
from sqlalchemy import func
from sqlalchemy.orm import aliased

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/<platform_name>')
def dashboard(platform_name=None):
	platforms = db.session.query(Platform).order_by(Platform.name.asc()).all()
	statuses = db.session.query(Category).filter_by(type='status').all()
	ownerships = db.session.query(Category).filter_by(type='ownership').all()
	digital_physical_options = db.session.query(Category).filter_by(type='digital_physical').all()

	selected_platform = None
	if platform_name:
		selected_platform = db.session.query(Platform).filter(Platform.name.ilike(platform_name)).first()
		if selected_platform:
			games = (
				db.session.query(Game)
				.filter_by(platform_id=selected_platform.id)
				.order_by(Game.title.asc())
				.all()
			)
		else:
			games = []
	else:
		games = db.session.query(Game).order_by(Game.title.asc()).all()

	# --- Summary calculations ---
	total_games = len(games)
	total_cost = sum(g.cost or 0 for g in games)

	# Peripherals: always global (not per platform)
	peripherals = db.session.query(Peripheral).all()
	total_peripherals = len(peripherals)
	total_peripherals_cost = sum(peripheral.cost or 0 for peripheral in peripherals)

	# Category counts
	if selected_platform:
		results = (
			db.session.query(Category.name, func.count(Game.id))
			.join(Game, Game.status_id == Category.id)
			.filter(Category.type == 'status', Game.platform_id == selected_platform.id)
			.group_by(Category.name)
			.all()
		)
		status_counts = {row[0]: row[1] for row in results}
	else:
		results = (
			db.session.query(Category.name, func.count(Game.id))
			.join(Game, Game.status_id == Category.id)
			.filter(Category.type == 'status')
			.group_by(Category.name)
			.all()
		)
		status_counts = {row[0]: row[1] for row in results}

	digital_counts = {d.name: 0 for d in digital_physical_options}
	for g in games:
		if g.digital_physical:
			digital_counts[g.digital_physical.name] = digital_counts.get(g.digital_physical.name, 0) + 1

	ownership_counts = {o.name: 0 for o in ownerships}
	for g in games:
		if g.ownership:
			ownership_counts[g.ownership.name] = ownership_counts.get(g.ownership.name, 0) + 1
	for p in peripherals:
		if p.ownership:
			ownership_counts[p.ownership.name] = ownership_counts.get(p.ownership.name, 0) + 1

	# --- Brand/platform breakdowns ---
	brands = {}
	for platform in platforms:
		brand = platform.name.split()[0] if ' ' in platform.name else platform.name
		if brand not in brands:
			brands[brand] = []
		brands[brand].append(platform)

	# Games by brand/platform
	brand_platform_stats = {}
	for brand, plats in brands.items():
		brand_platform_stats[brand] = {}
		for plat in plats:
			plat_games = [g for g in games if g.platform_id == plat.id]
			brand_platform_stats[brand][plat.name] = {
				'total': len(plat_games),
				'cost': sum(g.cost or 0 for g in plat_games),
				'status_counts': {s.name: 0 for s in statuses},
				'digital_counts': {d.name: 0 for d in digital_physical_options},
				'ownership_counts': {o.name: 0 for o in ownerships},
				'playing': [
					g
					for g in plat_games
					if g.status_id
					and any(s.id == g.status_id and s.name.lower() == 'playing' for s in statuses)
				],
				'backlog': [
					g
					for g in plat_games
					if g.status_id
					and any(s.id == g.status_id and s.name.lower() == 'backlog' for s in statuses)
				],
			}
			for g in plat_games:
				if g.status_id:
					status_obj = next((s for s in statuses if s.id == g.status_id), None)
					if status_obj:
						brand_platform_stats[brand][plat.name]['status_counts'][status_obj.name] += 1
				if g.digital_physical_id:
					dp_obj = next((d for d in digital_physical_options if d.id == g.digital_physical_id), None)
					if dp_obj:
						brand_platform_stats[brand][plat.name]['digital_counts'][dp_obj.name] += 1
				if g.ownership_id:
					own_obj = next((o for o in ownerships if o.id == g.ownership_id), None)
					if own_obj:
						brand_platform_stats[brand][plat.name]['ownership_counts'][own_obj.name] += 1

	# Playing/Backlog lists by platform
	playing_by_platform = {}
	backlog_by_platform = {}
	for plat in platforms:
		plat_games = [g for g in games if g.platform_id == plat.id]
		playing_by_platform[plat.name] = [
			g
			for g in plat_games
			if g.status_id
			and any(s.id == g.status_id and s.name.lower() == 'playing' for s in statuses)
		]
		backlog_by_platform[plat.name] = [
			g
			for g in plat_games
			if g.status_id
			and any(s.id == g.status_id and s.name.lower() == 'backlog' for s in statuses)
		]

	return render_template(
		'dashboard/dashboard.html',
		games=games,
		platforms=platforms,
		statuses=statuses,
		ownerships=ownerships,
		digital_physical_options=digital_physical_options,
		total_games=total_games,
		total_cost=total_cost,
		total_peripherals=total_peripherals,
		total_peripherals_cost=total_peripherals_cost,
		peripherals=peripherals,
		status_counts=status_counts,
		digital_counts=digital_counts,
		ownership_counts=ownership_counts,
		brand_platform_stats=brand_platform_stats,
		playing_by_platform=playing_by_platform,
		backlog_by_platform=backlog_by_platform,
		selected_platform=selected_platform,
	)
# --- Platform Management Routes ---
@bp.route('/platforms')
def platforms():
	platforms = db.session.query(Platform).order_by(Platform.name.asc()).all()
	return render_template('platforms/platforms.html', platforms=platforms)

@bp.route('/add_platform', methods=['GET', 'POST'])
def add_platform():
	if request.method == 'POST':
		name = request.form.get('name')
		manufacturer = request.form.get('manufacturer')
		release_year = request.form.get('release_year')
		generation = request.form.get('generation')
		description = request.form.get('description')
		cost = request.form.get('cost')
		quantity = request.form.get('quantity')
		purchased_from = request.form.get('purchased_from')
		ownership_id = request.form.get('ownership_id')
		notes = request.form.get('notes')
		new_platform = Platform(
			name=name,
			manufacturer=manufacturer,
			release_year=int(release_year) if release_year else None,
			generation=generation,
			description=description,
			cost=float(cost) if cost else None,
			quantity=int(quantity) if quantity else None,
			purchased_from=purchased_from,
			ownership_id=ownership_id or None,
			notes=notes
		)
		db.session.add(new_platform)
		db.session.commit()
		return redirect(url_for('main.platforms'))
	ownerships = db.session.query(Category).filter_by(type='ownership').all()
	return render_template('platforms/add_platform.html', ownerships=ownerships)

@bp.route('/edit_platform/<int:platform_id>', methods=['GET', 'POST'])
def edit_platform(platform_id):
	platform = db.session.get(Platform, platform_id)
	if platform is None:
		return "Platform not found", 404
	ownerships = db.session.query(Category).filter_by(type='ownership').all()
	if request.method == 'POST':
		platform.name = request.form.get('name', platform.name)
		platform.manufacturer = request.form.get('manufacturer', platform.manufacturer)
		release_year = request.form.get('release_year')
		platform.release_year = int(release_year) if release_year else None
		platform.generation = request.form.get('generation', platform.generation)
		platform.description = request.form.get('description', platform.description)
		cost = request.form.get('cost')
		platform.cost = float(cost) if cost else None
		quantity = request.form.get('quantity')
		platform.quantity = int(quantity) if quantity else None
		platform.purchased_from = request.form.get('purchased_from', platform.purchased_from)
		ownership_id = request.form.get('ownership_id')
		platform.ownership_id = int(ownership_id) if ownership_id else None
		platform.notes = request.form.get('notes', platform.notes)
		db.session.commit()
		return redirect(url_for('main.platforms'))
	return render_template('platforms/edit_platform.html', platform=platform, ownerships=ownerships)

@bp.route('/delete_platform/<int:platform_id>', methods=['POST'])
def delete_platform(platform_id):
	platform = db.session.get(Platform, platform_id)
	if platform is None:
		return "Platform not found", 404
	db.session.delete(platform)
	db.session.commit()
	return redirect(url_for('main.platforms'))

# ...existing code...
