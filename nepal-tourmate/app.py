from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import hashlib
import os
import uuid
from datetime import datetime, date
from algorithms.recommendation import RecommendationEngine
from algorithms.cost_estimator import TripCostEstimator

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'tourmate_secret_key')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'tourmate.db')


def load_local_env(env_path):
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r', encoding='utf-8') as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            if key.strip() and key.strip() not in os.environ:
                os.environ[key.strip()] = value.strip().strip('"').strip("'")


load_local_env(os.path.join(BASE_DIR, '.env'))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT,
        role TEXT DEFAULT 'user',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        destination TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        days INTEGER NOT NULL,
        difficulty TEXT DEFAULT 'Easy',
        season TEXT NOT NULL,
        transport TEXT NOT NULL,
        hotel_type TEXT NOT NULL,
        max_group_size INTEGER DEFAULT 10,
        image_url TEXT,
        short_description TEXT,
        description TEXT,
        featured INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        package_id INTEGER NOT NULL,
        travel_date TEXT NOT NULL,
        travelers INTEGER NOT NULL,
        transport_choice TEXT NOT NULL,
        hotel_choice TEXT NOT NULL,
        meal_plan TEXT NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        payment_status TEXT DEFAULT 'unpaid',
        payment_method TEXT,
        special_request TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(package_id) REFERENCES packages(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        method TEXT NOT NULL,
        transaction_id TEXT,
        status TEXT DEFAULT 'pending',
        provider_ref TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(booking_id) REFERENCES bookings(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@tourmate.com')
    admin_password = hash_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
    c.execute(
        'INSERT OR IGNORE INTO users (name, email, password, role, phone) VALUES (?, ?, ?, ?, ?)',
        ('Admin', admin_email, admin_password, 'admin', '9800000000')
    )

    package_count = c.execute('SELECT COUNT(*) FROM packages').fetchone()[0]
    if package_count == 0:
        packages = [
            (
                'Pokhara Adventure Escape', 'Pokhara', 'Adventure', 8500, 3, 'Easy', 'Spring', 'Tourist Bus', 'Standard', 12,
                'https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=1200&q=80',
                'Lakeside stay, boating, sunrise from Sarangkot and city sightseeing.',
                'A short and refreshing package for students, families and small groups. Includes lakeside accommodation, boating in Phewa Lake, Davis Falls, Gupteshwor Cave and sunrise view from Sarangkot.',
                1
            ),
            (
                'Mustang Heritage Trail', 'Mustang', 'Cultural', 24500, 5, 'Moderate', 'Autumn', 'Jeep', 'Deluxe', 8,
                'https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80',
                'A scenic mountain road trip through monasteries, caves and Himalayan landscapes.',
                'This package focuses on Upper Mustang culture, local villages, monastery visits and dry mountain landscapes. Best for travelers who love heritage and dramatic scenery.',
                1
            ),
            (
                'Chitwan Jungle Safari', 'Chitwan', 'Wildlife', 11000, 2, 'Easy', 'Winter', 'Tourist Bus', 'Resort', 10,
                'https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=80',
                'Jeep safari, Tharu culture and riverside wildlife experience.',
                'Designed for nature lovers. Includes jungle safari, canoe ride, Tharu cultural program and stay near the national park.',
                1
            ),
            (
                'Everest View Trek Lite', 'Solukhumbu', 'Trekking', 32000, 6, 'Challenging', 'Autumn', 'Flight', 'Tea House', 6,
                'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80',
                'A shorter Himalayan trekking package with unforgettable mountain panoramas.',
                'Perfect for those who want a trekking feel without a very long itinerary. Includes Lukla flight, guide support and tea house stay.',
                0
            ),
            (
                'Lumbini Peace Journey', 'Lumbini', 'Religious', 7000, 2, 'Easy', 'Winter', 'Bus', 'Standard', 15,
                'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=80',
                'Visit the birthplace of Lord Buddha with monastery and museum tour.',
                'Ideal for educational tours, family visits and spiritual travel. Covers Maya Devi Temple, monasteries, museum and peaceful garden spaces.',
                0
            ),
            (
                'Ilam Tea Garden Retreat', 'Ilam', 'Nature', 9800, 3, 'Easy', 'Monsoon', 'Jeep', 'Homestay', 10,
                'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80',
                'Green hills, tea gardens, sunrise points and local eastern food.',
                'A calm package for travelers who enjoy green landscapes, village hospitality and slow travel. Great for couples and small groups.',
                0
            )
        ]
        c.executemany('''
            INSERT INTO packages (
                title, destination, category, price, days, difficulty, season, transport, hotel_type,
                max_group_size, image_url, short_description, description, featured
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', packages)

    conn.commit()
    conn.close()


@app.template_filter('currency')
def currency_filter(value):
    return f"Rs. {float(value):,.0f}"


def require_login():
    return 'user_id' in session


def require_admin():
    return session.get('role') == 'admin'


@app.route('/')
def index():
    conn = get_db()
    featured = conn.execute('SELECT * FROM packages WHERE featured=1 ORDER BY id DESC LIMIT 3').fetchall()
    all_packages = conn.execute('SELECT * FROM packages ORDER BY id DESC LIMIT 6').fetchall()
    recommendations = []
    if session.get('user_id') and session.get('role') != 'admin':
        recommendations = RecommendationEngine().get_recommendations(session['user_id'], conn, top_n=3)
    conn.close()
    return render_template('index.html', featured=featured, all_packages=all_packages, recommendations=recommendations)


@app.route('/packages')
def packages():
    category = request.args.get('category', '').strip()
    search = request.args.get('search', '').strip()
    conn = get_db()
    query = 'SELECT * FROM packages WHERE 1=1'
    params = []
    if category:
        query += ' AND category=?'
        params.append(category)
    if search:
        query += ' AND (title LIKE ? OR destination LIKE ? OR category LIKE ?)'
        keyword = f'%{search}%'
        params.extend([keyword, keyword, keyword])
    query += ' ORDER BY featured DESC, id DESC'
    packages = conn.execute(query, params).fetchall()
    categories = [row['category'] for row in conn.execute('SELECT DISTINCT category FROM packages ORDER BY category').fetchall()]
    conn.close()
    return render_template('packages.html', packages=packages, categories=categories, selected_category=category, search=search)


@app.route('/package/<int:package_id>', methods=['GET', 'POST'])
def package_detail(package_id):
    conn = get_db()
    package = conn.execute('SELECT * FROM packages WHERE id=?', (package_id,)).fetchone()
    if not package:
        conn.close()
        flash('Package not found.', 'error')
        return redirect(url_for('packages'))

    if request.method == 'POST':
        if not require_login() or session.get('role') == 'admin':
            conn.close()
            flash('Please login as a user to book a package.', 'error')
            return redirect(url_for('login'))

        travel_date = request.form['travel_date']
        travelers = max(1, int(request.form['travelers']))
        transport_choice = request.form['transport_choice']
        hotel_choice = request.form['hotel_choice']
        meal_plan = request.form['meal_plan']
        special_request = request.form.get('special_request', '').strip()
        estimator = TripCostEstimator()
        result = estimator.calculate_total(
            base_price=package['price'],
            travelers=travelers,
            days=package['days'],
            transport_choice=transport_choice,
            hotel_choice=hotel_choice,
            meal_plan=meal_plan
        )
        total_amount = result['final_total']

        conn.execute('''
            INSERT INTO bookings (
                user_id, package_id, travel_date, travelers, transport_choice, hotel_choice,
                meal_plan, total_amount, special_request
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'], package_id, travel_date, travelers, transport_choice,
            hotel_choice, meal_plan, total_amount, special_request
        ))
        conn.commit()
        booking_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()
        flash('Package booked successfully. Please complete payment.', 'success')
        return redirect(url_for('payment_page', booking_id=booking_id))

    related = conn.execute(
        'SELECT * FROM packages WHERE category=? AND id != ? ORDER BY featured DESC, id DESC LIMIT 3',
        (package['category'], package_id)
    ).fetchall()
    conn.close()
    min_date = date.today().isoformat()
    return render_template('package_detail.html', package=package, related=related, min_date=min_date)


@app.route('/api/cost-estimate', methods=['POST'])
def cost_estimate():
    data = request.get_json(silent=True) or {}
    try:
        estimator = TripCostEstimator()
        result = estimator.calculate_total(
            base_price=float(data.get('base_price', 0)),
            travelers=max(1, int(data.get('travelers', 1))),
            days=max(1, int(data.get('days', 1))),
            transport_choice=str(data.get('transport_choice', 'Bus')),
            hotel_choice=str(data.get('hotel_choice', 'Standard')),
            meal_plan=str(data.get('meal_plan', 'Breakfast'))
        )
        return jsonify(result)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid input.'}), 400


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form['password']
        try:
            conn = get_db()
            conn.execute(
                'INSERT INTO users (name, email, password, phone) VALUES (?, ?, ?, ?)',
                (name, email, hash_password(password), phone)
            )
            conn.commit()
            conn.close()
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists.', 'error')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = hash_password(request.form['password'])
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email=? AND password=?', (email, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = user['role']
            flash('Login successful.', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))


@app.route('/dashboard')
def user_dashboard():
    if not require_login() or require_admin():
        return redirect(url_for('login'))
    conn = get_db()
    bookings = conn.execute('''
        SELECT b.*, p.title, p.destination, p.category, p.image_url
        FROM bookings b JOIN packages p ON b.package_id = p.id
        WHERE b.user_id=? ORDER BY b.id DESC
    ''', (session['user_id'],)).fetchall()
    recommendations = RecommendationEngine().get_recommendations(session['user_id'], conn, top_n=3)
    conn.close()
    return render_template('dashboard.html', bookings=bookings, recommendations=recommendations)


@app.route('/payment/<int:booking_id>')
def payment_page(booking_id):
    if not require_login() or require_admin():
        return redirect(url_for('login'))
    conn = get_db()
    booking = conn.execute('''
        SELECT b.*, p.title, p.destination, p.days
        FROM bookings b JOIN packages p ON b.package_id = p.id
        WHERE b.id=? AND b.user_id=?
    ''', (booking_id, session['user_id'])).fetchone()
    conn.close()
    if not booking:
        flash('Booking not found.', 'error')
        return redirect(url_for('user_dashboard'))
    return render_template('payment.html', booking=booking, khalti_configured=bool(os.environ.get('KHALTI_SECRET_KEY', '').strip()))


@app.route('/pay/khalti', methods=['POST'])
def pay_khalti():
    if not require_login() or require_admin():
        return redirect(url_for('login'))
    booking_id = int(request.form['booking_id'])
    conn = get_db()
    booking = conn.execute('SELECT * FROM bookings WHERE id=? AND user_id=?', (booking_id, session['user_id'])).fetchone()
    if not booking:
        conn.close()
        flash('Booking not found.', 'error')
        return redirect(url_for('user_dashboard'))

    transaction_id = f'KHALTI-{uuid.uuid4().hex[:10].upper()}'
    provider_ref = uuid.uuid4().hex[:12]
    conn.execute('UPDATE bookings SET payment_status=?, payment_method=?, status=? WHERE id=?', ('paid', 'khalti', 'confirmed', booking_id))
    conn.execute('''
        INSERT INTO payments (booking_id, user_id, amount, method, transaction_id, status, provider_ref)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (booking_id, session['user_id'], booking['total_amount'], 'khalti', transaction_id, 'success', provider_ref))
    conn.commit()
    conn.close()
    flash('Khalti payment completed successfully.', 'success')
    return redirect(url_for('payment_success', booking_id=booking_id))


@app.route('/pay/mobile', methods=['POST'])
def pay_mobile():
    if not require_login() or require_admin():
        return redirect(url_for('login'))
    booking_id = int(request.form['booking_id'])
    bank_name = request.form['bank_name'].strip()
    reference = request.form['reference'].strip()
    conn = get_db()
    booking = conn.execute('SELECT * FROM bookings WHERE id=? AND user_id=?', (booking_id, session['user_id'])).fetchone()
    if not booking:
        conn.close()
        flash('Booking not found.', 'error')
        return redirect(url_for('user_dashboard'))
    conn.execute('UPDATE bookings SET payment_status=?, payment_method=? WHERE id=?', ('pending_verification', 'mobile banking', booking_id))
    conn.execute('''
        INSERT INTO payments (booking_id, user_id, amount, method, transaction_id, status, provider_ref)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (booking_id, session['user_id'], booking['total_amount'], f'mobile banking - {bank_name}', reference, 'pending', reference))
    conn.commit()
    conn.close()
    flash('Mobile banking reference submitted. Admin will verify it.', 'success')
    return redirect(url_for('user_dashboard'))


@app.route('/pay/cash', methods=['POST'])
def pay_cash():
    if not require_login() or require_admin():
        return redirect(url_for('login'))
    booking_id = int(request.form['booking_id'])
    conn = get_db()
    booking = conn.execute('SELECT * FROM bookings WHERE id=? AND user_id=?', (booking_id, session['user_id'])).fetchone()
    if not booking:
        conn.close()
        flash('Booking not found.', 'error')
        return redirect(url_for('user_dashboard'))
    conn.execute('UPDATE bookings SET payment_status=?, payment_method=?, status=? WHERE id=?', ('cash_on_arrival', 'cash', 'confirmed', booking_id))
    conn.execute('''
        INSERT INTO payments (booking_id, user_id, amount, method, transaction_id, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (booking_id, session['user_id'], booking['total_amount'], 'cash', f'CASH-{booking_id}', 'reserved'))
    conn.commit()
    conn.close()
    flash('Cash on arrival selected. Your booking has been reserved.', 'success')
    return redirect(url_for('payment_success', booking_id=booking_id))


@app.route('/payment-success/<int:booking_id>')
def payment_success(booking_id):
    if not require_login() or require_admin():
        return redirect(url_for('login'))
    conn = get_db()
    booking = conn.execute('''
        SELECT b.*, p.title, p.destination, p.days
        FROM bookings b JOIN packages p ON b.package_id = p.id
        WHERE b.id=? AND b.user_id=?
    ''', (booking_id, session['user_id'])).fetchone()
    payment = conn.execute('SELECT * FROM payments WHERE booking_id=? ORDER BY id DESC LIMIT 1', (booking_id,)).fetchone()
    conn.close()
    if not booking:
        flash('Booking not found.', 'error')
        return redirect(url_for('user_dashboard'))
    return render_template('payment_success.html', booking=booking, payment=payment)


@app.route('/admin')
def admin_dashboard():
    if not require_admin():
        return redirect(url_for('login'))
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0]
    total_bookings = conn.execute('SELECT COUNT(*) FROM bookings').fetchone()[0]
    total_revenue = conn.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE status IN ('success','reserved')").fetchone()[0]
    pending_verifications = conn.execute("SELECT COUNT(*) FROM payments WHERE status='pending'").fetchone()[0]
    recent_bookings = conn.execute('''
        SELECT b.*, u.name AS user_name, p.title, p.destination
        FROM bookings b
        JOIN users u ON b.user_id=u.id
        JOIN packages p ON b.package_id=p.id
        ORDER BY b.id DESC LIMIT 8
    ''').fetchall()
    packages = conn.execute('SELECT * FROM packages ORDER BY id DESC').fetchall()
    users = conn.execute("SELECT * FROM users WHERE role='user' ORDER BY id DESC LIMIT 8").fetchall()
    pending_payments = conn.execute('''
        SELECT pay.*, u.name AS user_name, p.title
        FROM payments pay
        JOIN users u ON pay.user_id=u.id
        JOIN bookings b ON pay.booking_id=b.id
        JOIN packages p ON b.package_id=p.id
        WHERE pay.status='pending'
        ORDER BY pay.id DESC
    ''').fetchall()
    conn.close()
    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        total_bookings=total_bookings,
        total_revenue=total_revenue,
        pending_verifications=pending_verifications,
        recent_bookings=recent_bookings,
        packages=packages,
        users=users,
        pending_payments=pending_payments
    )


@app.route('/admin/package/add', methods=['POST'])
def admin_add_package():
    if not require_admin():
        return redirect(url_for('login'))
    form = request.form
    conn = get_db()
    conn.execute('''
        INSERT INTO packages (
            title, destination, category, price, days, difficulty, season, transport, hotel_type,
            max_group_size, image_url, short_description, description, featured
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        form['title'], form['destination'], form['category'], float(form['price']), int(form['days']),
        form['difficulty'], form['season'], form['transport'], form['hotel_type'], int(form['max_group_size']),
        form['image_url'], form['short_description'], form['description'], 1 if form.get('featured') == 'on' else 0
    ))
    conn.commit()
    conn.close()
    flash('New tour package added.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/booking/<int:booking_id>/<string:status>')
def admin_update_booking(booking_id, status):
    if not require_admin():
        return redirect(url_for('login'))
    allowed = {'confirmed', 'cancelled', 'completed'}
    if status not in allowed:
        flash('Invalid status.', 'error')
        return redirect(url_for('admin_dashboard'))
    conn = get_db()
    conn.execute('UPDATE bookings SET status=? WHERE id=?', (status, booking_id))
    conn.commit()
    conn.close()
    flash(f'Booking status updated to {status}.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/payment/<int:payment_id>/<string:action>')
def admin_verify_payment(payment_id, action):
    if not require_admin():
        return redirect(url_for('login'))
    conn = get_db()
    payment = conn.execute('SELECT * FROM payments WHERE id=?', (payment_id,)).fetchone()
    if not payment:
        conn.close()
        flash('Payment not found.', 'error')
        return redirect(url_for('admin_dashboard'))
    if action == 'approve':
        conn.execute("UPDATE payments SET status='success' WHERE id=?", (payment_id,))
        conn.execute("UPDATE bookings SET payment_status='paid', status='confirmed' WHERE id=?", (payment['booking_id'],))
        flash('Payment approved successfully.', 'success')
    elif action == 'reject':
        conn.execute("UPDATE payments SET status='failed' WHERE id=?", (payment_id,))
        conn.execute("UPDATE bookings SET payment_status='unpaid' WHERE id=?", (payment['booking_id'],))
        flash('Payment rejected.', 'error')
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/algorithm-explanation')
def algorithm_explanation():
    return render_template('algorithms.html')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
