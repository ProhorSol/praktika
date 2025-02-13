from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from models import db, User, Category, Request
from email_validator import validate_email, EmailNotValidError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB макс. размер файла

# Создаем папку для загрузок, если её нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

db.init_app(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return os.path.join('uploads', filename)
    return None

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    solved_count = Request.query.filter_by(status='Решена').count()
    return render_template('index.html', solved_count=solved_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Неверное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')
        privacy_policy = request.form.get('privacy_policy')

        if not privacy_policy:
            flash('Необходимо согласиться с политикой конфиденциальности', 'error')
            return redirect(url_for('register'))

        if not username or not email or not password or not confirm_password:
            flash('Пожалуйста, заполните все поля', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'error')
            return redirect(url_for('register'))

        try:
            validate_email(email)
        except EmailNotValidError:
            flash('Указан некорректный email адрес', 'error')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.password = generate_password_hash(password)
        db.session.add(user)
        db.session.commit()

        flash('Регистрация успешна! Теперь вы можете войти', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    status_filter = request.args.get('status')
    category_filter = request.args.get('category')
    
    query = Request.query.filter_by(user_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    
    requests = query.order_by(Request.created_at.desc()).all()
    categories = Category.query.all()
    
    return render_template('dashboard.html', requests=requests, categories=categories)

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Доступ запрещен')
        return redirect(url_for('dashboard'))
    
    status_filter = request.args.get('status')
    category_filter = request.args.get('category')
    
    query = Request.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    
    requests = query.order_by(Request.created_at.desc()).all()
    categories = Category.query.all()
    
    return render_template('admin_dashboard.html', requests=requests, categories=categories)

@app.route('/request/create', methods=['GET', 'POST'])
@login_required
def create_request():
    if request.method == 'POST':
        # Проверка наличия всех необходимых полей
        if not all(field in request.form for field in ['title', 'description', 'category_id']):
            flash('Пожалуйста, заполните все поля')
            return redirect(url_for('create_request'))
        
        # Проверка загруженного файла
        if 'before_image' not in request.files:
            flash('Необходимо загрузить фотографию')
            return redirect(url_for('create_request'))
        
        before_image = request.files['before_image']
        image_path = save_image(before_image)
        
        if not image_path:
            flash('Ошибка при загрузке изображения')
            return redirect(url_for('create_request'))
        
        # Создание новой заявки
        new_request = Request(
            title=request.form['title'],
            description=request.form['description'],
            category_id=request.form['category_id'],
            user_id=current_user.id,
            before_image=image_path
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        flash('Заявка успешно создана')
        return redirect(url_for('dashboard'))
    
    categories = Category.query.all()
    return render_template('create_request.html', categories=categories)

@app.route('/request/<int:request_id>/delete')
@login_required
def delete_request(request_id):
    req = Request.query.get_or_404(request_id)
    
    if req.user_id != current_user.id and not current_user.is_admin:
        flash('Доступ запрещен')
        return redirect(url_for('dashboard'))
    
    if req.status != 'Новая':
        flash('Можно удалять только новые заявки')
        return redirect(url_for('dashboard'))
    
    # Удаление файлов
    if req.before_image:
        try:
            os.remove(os.path.join(app.static_folder, req.before_image))
        except:
            pass
    
    if req.after_image:
        try:
            os.remove(os.path.join(app.static_folder, req.after_image))
        except:
            pass
    
    db.session.delete(req)
    db.session.commit()
    
    flash('Заявка удалена')
    return redirect(url_for('dashboard'))

@app.route('/request/<int:request_id>/resolve', methods=['POST'])
@login_required
def resolve_request(request_id):
    if not current_user.is_admin:
        flash('Доступ запрещен')
        return redirect(url_for('dashboard'))
    
    req = Request.query.get_or_404(request_id)
    
    if req.status != 'Новая':
        flash('Можно решать только новые заявки')
        return redirect(url_for('admin_dashboard'))
    
    if 'after_image' not in request.files:
        flash('Необходимо загрузить фотографию результата')
        return redirect(url_for('admin_dashboard'))
    
    after_image = request.files['after_image']
    image_path = save_image(after_image)
    
    if not image_path:
        flash('Ошибка при загрузке изображения')
        return redirect(url_for('admin_dashboard'))
    
    req.status = 'Решена'
    req.after_image = image_path
    db.session.commit()
    
    flash('Заявка помечена как решенная')
    return redirect(url_for('admin_dashboard'))

@app.route('/request/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_request(request_id):
    if not current_user.is_admin:
        flash('Доступ запрещен')
        return redirect(url_for('dashboard'))
    
    req = Request.query.get_or_404(request_id)
    
    if req.status != 'Новая':
        flash('Можно отклонять только новые заявки')
        return redirect(url_for('admin_dashboard'))
    
    if 'rejection_reason' not in request.form or not request.form['rejection_reason'].strip():
        flash('Необходимо указать причину отклонения')
        return redirect(url_for('admin_dashboard'))
    
    req.status = 'Отклонена'
    req.rejection_reason = request.form['rejection_reason']
    db.session.commit()
    
    flash('Заявка отклонена')
    return redirect(url_for('admin_dashboard'))

@app.route('/category/add', methods=['POST'])
@login_required
def add_category():
    if not current_user.is_admin:
        flash('Доступ запрещен')
        return redirect(url_for('dashboard'))
    
    if 'category_name' not in request.form or not request.form['category_name'].strip():
        flash('Необходимо указать название категории')
        return redirect(url_for('admin_dashboard'))
    
    category_name = request.form['category_name'].strip()
    
    if Category.query.filter_by(name=category_name).first():
        flash('Категория с таким названием уже существует')
        return redirect(url_for('admin_dashboard'))
    
    category = Category(name=category_name)
    db.session.add(category)
    db.session.commit()
    
    flash('Категория добавлена')
    return redirect(url_for('admin_dashboard'))

@app.route('/category/<int:category_id>/delete')
@login_required
def delete_category(category_id):
    if not current_user.is_admin:
        flash('Доступ запрещен')
        return redirect(url_for('dashboard'))
    
    category = Category.query.get_or_404(category_id)
    
    # Удаление всех связанных заявок и их изображений
    for req in category.requests:
        if req.before_image:
            try:
                os.remove(os.path.join(app.static_folder, req.before_image))
            except:
                pass
        if req.after_image:
            try:
                os.remove(os.path.join(app.static_folder, req.after_image))
            except:
                pass
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Категория и все связанные заявки удалены')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Создание администратора, если его нет
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()

        # Создание базовых категорий, если их нет
        default_categories = [
            'Ремонт и обслуживание',
            'Уборка территории',
            'Освещение',
            'Водоснабжение',
            'Отопление',
            'Электрика',
            'Сантехника',
            'Благоустройство',
            'Безопасность',
            'Прочее'
        ]

        for category_name in default_categories:
            if not Category.query.filter_by(name=category_name).first():
                category = Category(name=category_name)
                db.session.add(category)
        
        db.session.commit()

    app.run(debug=True)
