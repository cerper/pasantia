import os
from flask import Flask, render_template, render_template_string, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
from flask_migrate import Migrate
from sqlalchemy_utils import database_exists, create_database 
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = '1234'

# Conexión a MariaDB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mariadb+mariadbconnector://david:1234@localhost:3306/proyecto_movilnet'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', "jfif"}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELOS DE DATOS (Roles y Usuarios) ---
roles_usuarios = db.Table('roles_usuarios',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)

class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)
    roles = db.relationship('Role', secondary=roles_usuarios, backref=db.backref('usuarios', lazy='dynamic'))

    def tiene_rol(self, nombre_rol):
        return any(role.nombre == nombre_rol for role in self.roles)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
        create_database(app.config['SQLALCHEMY_DATABASE_URI'])
    db.create_all()

    # Insertar roles por defecto si no existen
    roles_iniciales = ['Admin', 'Usuario']
    for r in roles_iniciales:
        if not Role.query.filter_by(nombre=r).first():
            db.session.add(Role(nombre=r))
    db.session.commit()
def allowed_file(filename):
    """Return True if filename has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# --- DECORADOR PERSONALIZADO PARA CONTROL DE ROLES ---
def requiere_rol(nombre_rol):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.tiene_rol(nombre_rol):
                return "Acceso denegado: No tienes el rol necesario.", 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- RUTAS ---
@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form.get("correo")
        contraseña = request.form.get("contraseña")
        usuario = User.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.contraseña, contraseña):
            login_user(usuario)
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('reportes'))
        else:
            flash('Correo o contraseña incorrectos.', 'error')
            return redirect(url_for('index'))
    return render_template("index.html")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("correo")
        contraseña = request.form.get("contraseña")
        rol = request.form.get("rol")

        if not nombre or not email or not contraseña or not rol:
            flash('Por favor completa todos los campos.', 'error')
            return redirect(url_for('registro'))

        rol_obj = Role.query.filter_by(nombre=rol).first()
       

        try:
            password_hashed = generate_password_hash(contraseña)
            nuevo_usuario = User(
                nombre=nombre,
                email=email,
                contraseña=password_hashed,
                roles=[rol_obj]
            )
            
            # Persistencia en base de datos
            db.session.add(nuevo_usuario)
            db.session.commit()  
            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('index'))

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error de Base de Datos: {e}")
            flash('Ocurrió un error al guardar el usuario.', 'error')
            return redirect(url_for('registro'))

    return render_template("registro.html")
@app.route("/reportes")
@login_required
def reportes():
    return render_template("reportes.html")


if __name__ == '__main__':
    app.run(debug=True)