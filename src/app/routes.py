from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Game, Category, Peripheral, Platform
from core.database import db
import csv
from io import TextIOWrapper
from sqlalchemy import func
from sqlalchemy.orm import aliased

bp = Blueprint('main', __name__)

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

# Dashboard route: summary tables by category
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
            games = db.session.query(Game).filter_by(platform_id=selected_platform.id).order_by(Game.title.asc()).all()
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
        status_counts = dict(
            db.session.query(Category.name, func.count(Game.id)) # type: ignore
            .join(Game, Game.status_id == Category.id)
            .filter(Category.type == 'status', Game.platform_id == selected_platform.id)  # type: ignore
            .group_by(Category.name) # type: ignore
            .all()
        )
    else:
        status_counts = dict(
            db.session.query(Category.name, func.count(Game.id)) # type: ignore
            .join(Game, Game.status_id == Category.id)
            .filter(Category.type == 'status') # type: ignore
            .group_by(Category.name) # type: ignore
            .all()
        )

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
                'playing': [g for g in plat_games if g.status_id and any(s.id == g.status_id and s.name.lower() == 'playing' for s in statuses)],
                'backlog': [g for g in plat_games if g.status_id and any(s.id == g.status_id and s.name.lower() == 'backlog' for s in statuses)],
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
        playing_by_platform[plat.name] = [g for g in plat_games if g.status_id and any(s.id == g.status_id and s.name.lower() == 'playing' for s in statuses)]
        backlog_by_platform[plat.name] = [g for g in plat_games if g.status_id and any(s.id == g.status_id and s.name.lower() == 'backlog' for s in statuses)]

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
        selected_platform=selected_platform
    )

# Route to reset the database (delete all games and categories, reseed categories)
@bp.route('/reset_db', methods=['GET', 'POST'])
def reset_db():
    if request.method == 'POST':
        db.session.query(Game).delete()
        db.session.query(Peripheral).delete()
        db.session.query(Category).delete()
        db.session.commit()
        # Reseed categories
        categories = [
            Category(name='PS4', type='platform'),
            Category(name='PS5', type='platform'),
            Category(name='Xbox', type='platform'),
            Category(name='PC', type='platform'),
            Category(name='Switch', type='platform'),
            Category(name='Other', type='platform'),
            Category(name='Playing', type='status'),
            Category(name='Backlog', type='status'),
            Category(name='Beaten', type='status'),
            Category(name='Completed', type='status'),
            Category(name='Abandoned', type='status'),
            Category(name='Own', type='ownership'),
            Category(name='Borrowed', type='ownership'),
            Category(name='Digital', type='digital_physical'),
            Category(name='Physical', type='digital_physical'),
            Category(name='Both', type='digital_physical'),
        ]
        db.session.add_all(categories)
        db.session.commit()

        # Optionally, add a sample Peripheral for demonstration (remove if not needed)
        ps4_platform = db.session.query(Category).filter_by(name='PS4', type='platform').first()
        own_ownership = db.session.query(Category).filter_by(name='Own', type='ownership').first()
        if ps4_platform and own_ownership:
            db.session.add(Peripheral(
                name='PS4 Controller',
                platform_id=ps4_platform.id,
                peripheral_type='Controller',
                platform_type='PS4',
                cost=59.99,
                quantity=1,
                purchased_from='GameStop',
                ownership_id=own_ownership.id,
                notes='Reset sample peripheral'
            ))
            db.session.commit()

        return render_template('admin/reset_db.html', message='Database has been reset!')
    return render_template('admin/reset_db.html', message=None)

# Old index route for add/view (can be linked from dashboard)
@bp.route('/collection')
@bp.route('/collection/<platform_name>')
def index(platform_name=None):
    # Use Platform table for platforms
    platforms = db.session.query(Platform).order_by(Platform.name.asc()).all()
    statuses = db.session.query(Category).filter_by(type='status').all()
    ownerships = db.session.query(Category).filter_by(type='ownership').all()
    digital_physical_options = db.session.query(Category).filter_by(type='digital_physical').all()

    # If no platform_name, redirect to the first platform tab
    if not platform_name and platforms:
        return redirect(url_for('main.index', platform_name=platforms[0].name))

    selected_platform = None
    games = []
    peripherals = []
    grade_filter = request.args.get('grade')
    if platform_name:
        # Case-insensitive match for platform name in Platform table
        platform = db.session.query(Platform).filter(Platform.name.ilike(platform_name)).first()
        if platform:
            selected_platform = platform
            query = db.session.query(Game).filter_by(platform_id=platform.id)
            if grade_filter:
                query = query.filter(Game.grade == grade_filter)
            games = query.order_by(Game.title.asc()).all()

    return render_template(
        "games/index.html",
        games=games,
        peripherals=peripherals,
        platforms=platforms,
        statuses=statuses,
        ownerships=ownerships,
        digital_physical_options=digital_physical_options,
        selected_platform=selected_platform
    )

# @bp.route('/collections/<platform_name>')
# def index(platform_name=None):
#     platforms = Category.query.all()
#     return str(platforms)
# Admin: Manage Platforms
@bp.route('/admin/platforms', methods=['GET', 'POST'])
def admin_platforms():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name')
            if name:
                db.session.add(Category(name=name, type='platform'))
                db.session.commit()
                flash('Platform added.')
        elif action == 'edit':
            platform_id = request.form.get('platform_id')
            name = request.form.get('name')
            platform = db.session.query(Category).filter_by(id=platform_id, type='platform').first()
            if platform and name:
                platform.name = name
                db.session.commit()
                flash('Platform updated.')
        elif action == 'delete':
            platform_id = request.form.get('platform_id')
            platform = db.session.query(Category).filter_by(id=platform_id, type='platform').first()
            if platform:
                db.session.delete(platform)
                db.session.commit()
                flash('Platform deleted.')
    platforms = db.session.query(Category).filter_by(type='platform').all()
    return render_template('admin/platforms.html', platforms=platforms)

@bp.route('/add_game', methods=['POST'])
def add_game():
    platform_id = request.form.get('platform_id')
    title = request.form.get('title')
    cost = request.form.get('cost')
    status_id = request.form.get('status_id')
    ownership_id = request.form.get('ownership_id')
    digital_physical_id = request.form.get('digital_physical_id')
    notes = request.form.get('notes')
    image_url = request.form.get('image_url')
    grade = request.form.get('grade')
    new_game = Game(
        title=title,
        platform_id=platform_id,
        cost=float(cost) if cost else None,
        status_id=status_id or None,
        ownership_id=ownership_id or None,
        digital_physical_id=digital_physical_id or None,
        notes=notes,
        image_url=image_url,
        grade=grade or None,
        type="game"
    )
    db.session.add(new_game)
    db.session.commit()
    platform = db.session.get(Platform, platform_id)
    if platform:
        return redirect(url_for('main.index', platform_name=platform.name))
    return redirect(url_for('main.index'))

# Edit game route (form and update logic)
@bp.route('/edit/<int:game_id>', methods=['GET', 'POST'])
def edit_game(game_id):
    game = db.session.get(Game, game_id)
    if game is None:
        return "Game not found", 404
    platforms = db.session.query(Platform).all()
    statuses = db.session.query(Category).filter_by(type='status').all()
    ownerships = db.session.query(Category).filter_by(type='ownership').all()
    digital_physical_options = db.session.query(Category).filter_by(type='digital_physical').all()
    if request.method == 'POST':
        game.title = request.form['title']
        game.platform_id = int(request.form['platform_id'])
        cost = request.form.get('cost')
        game.cost = float(cost) if cost else None
        status_id = request.form.get('status_id')
        game.status_id = int(status_id) if status_id else None
        ownership_id = request.form.get('ownership_id')
        game.ownership_id = int(ownership_id) if ownership_id else None
        digital_physical_id = request.form.get('digital_physical_id')
        game.digital_physical_id = int(digital_physical_id) if digital_physical_id else None
        game.notes = request.form.get('notes')
        game.image_url = request.form.get('image_url')
        game.grade = request.form.get('grade') or None
        db.session.commit()
        return redirect(url_for('main.index', platform_name=game.platform.name))
    return render_template('games/edit_game.html', game=game, platforms=platforms, statuses=statuses, ownerships=ownerships, digital_physical_options=digital_physical_options)

# Admin: Manage Statuses
@bp.route('/admin/statuses', methods=['GET', 'POST'])
def admin_statuses():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name')
            if name:
                db.session.add(Category(name=name, type='status'))
                db.session.commit()
        elif action == 'edit':
            status_id = request.form.get('status_id')
            name = request.form.get('name')
            status = db.session.query(Category).filter_by(id=status_id, type='status').first()
            if status and name:
                status.name = name
                db.session.commit()
        elif action == 'delete':
            status_id = request.form.get('status_id')
            status = db.session.query(Category).filter_by(id=status_id, type='status').first()
            if status:
                db.session.delete(status)
                db.session.commit()
    statuses = db.session.query(Category).filter_by(type='status').all()
    return render_template('admin/statuses.html', statuses=statuses)

# Admin: Manage Ownerships
@bp.route('/admin/ownerships', methods=['GET', 'POST'])
def admin_ownerships():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name')
            if name:
                db.session.add(Category(name=name, type='ownership'))
                db.session.commit()
        elif action == 'edit':
            ownership_id = request.form.get('ownership_id')
            name = request.form.get('name')
            ownership = db.session.query(Category).filter_by(id=ownership_id, type='ownership').first()
            if ownership and name:
                ownership.name = name
                db.session.commit()
        elif action == 'delete':
            ownership_id = request.form.get('ownership_id')
            ownership = db.session.query(Category).filter_by(id=ownership_id, type='ownership').first()
            if ownership:
                db.session.delete(ownership)
                db.session.commit()
    ownerships = db.session.query(Category).filter_by(type='ownership').all()
    return render_template('admin/ownerships.html', ownerships=ownerships)

# Admin: Manage Digital/Physical
@bp.route('/admin/digitalphysical', methods=['GET', 'POST'])
def admin_digitalphysical():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name')
            if name:
                db.session.add(Category(name=name, type='digital_physical'))
                db.session.commit()
        elif action == 'edit':
            dp_id = request.form.get('dp_id')
            name = request.form.get('name')
            dp = db.session.query(Category).filter_by(id=dp_id, type='digital_physical').first()
            if dp and name:
                dp.name = name
                db.session.commit()
        elif action == 'delete':
            dp_id = request.form.get('dp_id')
            dp = db.session.query(Category).filter_by(id=dp_id, type='digital_physical').first()
            if dp:
                db.session.delete(dp)
                db.session.commit()
    digital_physical_options = db.session.query(Category).filter_by(type='digital_physical').all()
    return render_template('admin/digitalphysical.html', digital_physical_options=digital_physical_options)

# Import games from CSV
@bp.route('/import', methods=['GET', 'POST'])
def import_games():
    platforms = db.session.query(Platform).order_by(Platform.name.asc()).all()
    statuses = db.session.query(Category).filter_by(type='status').all()
    ownerships = db.session.query(Category).filter_by(type='ownership').all()
    digital_physical_options = db.session.query(Category).filter_by(type='digital_physical').all()
    message = None
    # If no platforms exist, redirect to add_platform
    if not platforms:
        flash('No platforms found. Please add a platform before importing games.')
        return redirect(url_for('main.add_platform'))
    if request.method == 'POST':
        file = request.files.get('csvfile')
        platform_id = request.form.get('platform_id')
        platform = db.session.query(Platform).filter_by(id=platform_id).first() if platform_id else None
        if file and file.filename and file.filename.lower().endswith('.csv') and platform:
            all_lines = TextIOWrapper(file.stream, encoding='utf-8').readlines()
            header_idx = None
            for idx, line in enumerate(all_lines):
                if line.strip().startswith('Game,'):
                    header_idx = idx
                    break
            if header_idx is not None:
                data_lines = all_lines[header_idx:]
                reader = csv.DictReader(data_lines)
                imported = 0
                skipped = 0
                skipped_titles = []
                for row in reader:
                    row = {k.strip(): (v.strip() if v else v) for k, v in row.items()}
                    mapped = {
                        'Title': row.get('Title') or row.get('Game') or '',
                        'Cost': row.get('Cost'),
                        'Status': row.get('Status'),
                        'Ownership': row.get('Ownership'),
                        'Digital/Physical': row.get('Digital/Physical') or row.get('Boxed/Digital'),
                        'Grade': row.get('Grade'),
                        'Notes': row.get('Notes'),
                        'Image URL': row.get('Image URL')
                    }
                    game_title = mapped['Title']
                    if not game_title or not game_title.strip() or game_title.strip().lower() in ['total owned games', 'game']:
                        continue
                    # Check for duplicate (same title and platform)
                    existing = db.session.query(Game).filter_by(title=game_title.strip(), platform_id=platform.id).first()
                    if existing:
                        skipped += 1
                        skipped_titles.append(game_title.strip())
                        continue  # Skip duplicate
                    status_val = (mapped['Status'] or '').strip()
                    status = next((s for s in statuses if s.name.lower() == status_val.lower()), None)
                    ownership_val = (mapped['Ownership'] or '').strip()
                    ownership = next((o for o in ownerships if o.name.lower() == ownership_val.lower()), None)
                    dp_val = (mapped['Digital/Physical'] or '').strip()
                    dp = next((d for d in digital_physical_options if d.name.lower() == dp_val.lower()), None)
                    cost = mapped['Cost']
                    try:
                        if cost:
                            cost = cost.replace('$','').replace(',','')
                        cost = float(cost) if cost else None
                    except Exception:
                        cost = None
                    notes = mapped['Notes']
                    image_url = mapped['Image URL']
                    grade = mapped['Grade']
                    new_game = Game(
                        title=game_title,
                        platform_id=platform.id,
                        cost=cost,
                        status_id=status.id if status else None,
                        ownership_id=ownership.id if ownership else None,
                        digital_physical_id=dp.id if dp else None,
                        notes=notes,
                        image_url=image_url,
                        grade=grade or None
                    )
                    db.session.add(new_game)
                    imported += 1
                db.session.commit()
                message = f"Imported {imported} games for platform {platform.name} from CSV. Skipped {skipped} duplicates." \
                    + (f" Skipped titles: {', '.join(skipped_titles)}" if skipped_titles else "")
            else:
                message = "Could not find header row in CSV. Please check the file format."
    return render_template('games/import_games.html', platforms=platforms, statuses=statuses, ownerships=ownerships, digital_physical_options=digital_physical_options, message=message)

@bp.route('/add_peripheral', methods=['POST'])
def add_peripheral():
    platform_id = request.form['platform_id']
    name = request.form.get('name', '')
    peripheral_type = request.form.get('peripheral_type', '')
    cost = request.form.get('cost')
    quantity = request.form.get('quantity')
    purchased_from = request.form.get('purchased_from')
    ownership_id = request.form.get('ownership_id')
    notes = request.form.get('notes')
    platform_type = request.form.get('platform_type')
    peripheral_kwargs = {
        'name': name,
        'platform_id': platform_id,
        'cost': float(cost) if cost else None,
        'purchased_from': purchased_from,
        'notes': notes,
        'ownership_id': ownership_id or None,
        'peripheral_type': peripheral_type,
        'platform_type': platform_type
    }
    if quantity:
        peripheral_kwargs['quantity'] = int(quantity)
    new_peripheral = Peripheral(**peripheral_kwargs)
    db.session.add(new_peripheral)
    db.session.commit()
    platform = db.session.get(Platform, platform_id)
    if platform:
        return redirect(url_for('main.index', platform_name=platform.name))
    return redirect(url_for('main.index'))

# Edit peripheral route (form and update logic)
@bp.route('/edit_peripheral/<int:peripheral_id>', methods=['GET', 'POST'])
def edit_peripheral(peripheral_id):
    peripheral = db.session.get(Peripheral, peripheral_id)
    if peripheral is None:
        return "Peripheral not found", 404
    platforms = db.session.query(Platform).all()
    ownerships = db.session.query(Category).filter_by(type='ownership').all()
    if request.method == 'POST':
        from flask import current_app
        current_app.logger.debug(f"edit_peripheral POST request.form: {dict(request.form)}")
        peripheral.name = request.form.get('name', peripheral.name)
        peripheral.peripheral_type = request.form.get('peripheral_type', peripheral.peripheral_type)
        peripheral.platform_type = request.form.get('platform_type', peripheral.platform_type)
        peripheral.platform_id = int(request.form.get('platform_id', peripheral.platform_id))
        peripheral.cost = float(request.form.get('cost', peripheral.cost) or 0)
        peripheral.quantity = int(request.form.get('quantity', peripheral.quantity) or 0)
        peripheral.purchased_from = request.form.get('purchased_from', peripheral.purchased_from)
        ownership_id = request.form.get('ownership_id')
        peripheral.ownership_id = int(ownership_id) if ownership_id else None
        peripheral.notes = request.form.get('notes', peripheral.notes)
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('peripherals/edit_peripheral.html', peripheral=peripheral, platforms=platforms, ownerships=ownerships)

@bp.route('/delete_game/<int:game_id>', methods=['POST'])
def delete_game(game_id):
    game = db.session.get(Game, game_id)
    if game is None:
        return "Game not found", 404
    platform = game.platform.name if game.platform else None
    db.session.delete(game)
    db.session.commit()
    if platform:
        return redirect(url_for('main.index', platform_name=platform))
    return redirect(url_for('main.index'))

@bp.route('/delete_peripheral/<int:peripheral_id>', methods=['POST'])
def delete_peripheral(peripheral_id):
    peripheral = db.session.get(Peripheral, peripheral_id)
    if peripheral is None:
        return "Peripheral not found", 404
    platform = peripheral.platform.name if peripheral.platform else None
    db.session.delete(peripheral)
    db.session.commit()
    if platform:
        return redirect(url_for('main.index', platform_name=platform))
    return redirect(url_for('main.index'))

# Peripherals: dedicated route for listing and adding peripherals
@bp.route('/peripherals', methods=['GET', 'POST'])
def peripherals():
    ownerships = db.session.query(Category).filter_by(type='ownership').all()
    platforms = db.session.query(Platform).order_by(Platform.name.asc()).all()
    if request.method == 'POST':
        name = request.form.get('name', '')
        peripheral_type = request.form.get('peripheral_type', '')
        platform_type = request.form.get('platform_type', '')
        cost = request.form.get('cost')
        quantity = request.form.get('quantity')
        purchased_from = request.form.get('purchased_from')
        ownership_id = request.form.get('ownership_id')
        notes = request.form.get('notes')
        platform_id = request.form.get('platform_id')
        try:
            platform_id = int(platform_id) if platform_id else None
        except Exception:
            platform_id = None
        if not platform_id:
            flash('Platform is required for a peripheral.', 'danger')
            peripherals = db.session.query(Peripheral).all()
            return render_template('peripherals/add_peripheral.html', peripherals=peripherals, ownerships=ownerships, platforms=platforms)
        peripheral = Peripheral(
            name=name,
            peripheral_type=peripheral_type,
            platform_type=platform_type,
            cost=float(cost) if cost else None,
            quantity=int(quantity) if quantity else None,
            purchased_from=purchased_from,
            ownership_id=ownership_id or None,
            notes=notes,
            platform_id=platform_id
        )
        db.session.add(peripheral)
        db.session.commit()
        return redirect(url_for('main.peripherals'))
    peripherals = db.session.query(Peripheral).all()
    return render_template('peripherals/add_peripheral.html', peripherals=peripherals, ownerships=ownerships, platforms=platforms)