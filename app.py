from flask import Flask, render_template, render_template_string, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SECRET_KEY'] = '1234'

# Conexión a MariaDB (sustituye usuario, password, host y db_name)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mariadb+mariadbconnector://david:1234@localhost:3306/proyecto_movilnet'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False) 
    email = db.Column(db.String(80), unique=True, nullable=False)
    contraseña= db.Column(db.String(80), unique=True, nullable=False)
    roles = db.relationship('Role', secondary=roles_usuarios, backref=db.backref('usuarios', lazy='dynamic'))

    def tiene_rol(self, nombre_rol):
        return any(role.nombre == nombre_rol for role in self.roles)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
@app.route('/' ,methods=["GET", "POST"])
def index():
        if request.method == "POST":
            email= request.form.get("correo")
            contraseña = request.form.get("contraseña")  
            usuario = User.query.filter_by(email=email, contraseña=contraseña).first()
            if usuario:
                login_user(usuario)
                flash('¡Inicio de sesión exitoso!', 'success')
                return redirect(url_for('reportes'))
            else:
                flash('Correo o contraseña incorrectos.', 'error')
                return redirect(url_for('index'))
        return render_template("index.html")


@app.route("/registro", methods=["GET", "POST"])
@login_required
@requiere_rol("admin")  # Solo los administradores pueden registrar nuevos usuarios
def registro():

    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("correo")
        contraseña = request.form.get("contraseña")
        rol = request.form.get("rol")
        rol_obj = Role.query.filter_by(nombre=rol).first()  # O buscar por ID
        if rol_obj is None:
            flash('El rol seleccionado no existe.', 'error')
            return redirect(url_for('registro'))
        nuevo_usuario = User(nombre=nombre, email=email, contraseña=contraseña, roles=[rol_obj])
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('reportes'))

    return render_template("registro.html")

@app.route("/reportes")
#@login_required
#@requiere_rol("admin", "user")
def reportes():
    return render_template("reportes.html")

if __name__ == '__main__':
   app.run(debug=True, host='0.0.0.0', port=5004)