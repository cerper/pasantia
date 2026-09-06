import os
import json
import uuid
from flask import Flask, render_template, render_template_string, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
from flask_migrate import Migrate
from sqlalchemy_utils import database_exists, create_database 
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import enum

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
    nombre = db.Column(db.String(50),  nullable=False)
    apellido = db.Column(db.String(50),  nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)
    roles = db.relationship('Role', secondary=roles_usuarios, backref=db.backref('usuarios', lazy='dynamic'))

    def tiene_rol(self, nombre_rol):
        return any(role.nombre == nombre_rol for role in self.roles)
# --- ENUMS ---
class EstadoReporte(enum.Enum):
    BORRADOR = "Borrador"
    PENDIENTE = "Pendiente"
    APROBADO = "Aprobado"
    

class EscenarioCategoria(enum.Enum):
    NEUTRAL = "Neutral"
    FAVORABLE = "Favorable"
    DESFAVORABLE = "Desfavorable"


#  TABLA PRINCIPAL DEL REPORTE
class ReporteCompetencia(db.Model):
    __tablename__ = "reportes_competencia"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    estado = db.Column(
        db.Enum(EstadoReporte),
        nullable=False,
        default=EstadoReporte.BORRADOR,
        index=True,
    )
    tipo_reporte = db.Column(
        db.String(50), nullable=False, default="competencia"
    )

    # Situación actual
    situacion_movistar = db.Column(db.Text, nullable=True)
    situacion_digitel = db.Column(db.Text, nullable=True)

    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relaciones
    escenarios = db.relationship(
        "EscenarioAccion", backref="reporte", cascade="all, delete-orphan"
    )
    seguimientos = db.relationship(
        "SeguimientoCampana", backref="reporte", cascade="all, delete-orphan"
    )


#  TABLA PARA MÚLTIPLES ESCENARIOS (1:N)
class EscenarioAccion(db.Model):
    __tablename__ = "escenarios_accion"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reporte_id = db.Column(
        db.Integer,
        db.ForeignKey("reportes_competencia.id", ondelete="CASCADE"),
        nullable=False,
    )

    categoria = db.Column(
        db.Enum(EscenarioCategoria),
        nullable=False,
        default=EscenarioCategoria.NEUTRAL,
    )
    analisis = db.Column(db.Text, nullable=True)
    curso_accion = db.Column(db.Text, nullable=True)


#  TABLA PARA EL SEGUIMIENTO POR OPERADORA (Movistar / Digitel)
class SeguimientoCampana(db.Model):
    __tablename__ = "seguimiento_campanas"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reporte_id = db.Column(
        db.Integer,
        db.ForeignKey("reportes_competencia.id", ondelete="CASCADE"),
        nullable=False,
    )

    operadora = db.Column(
        db.String(20), nullable=False
    )  # 'Movistar' o 'Digitel'
    analisis = db.Column(db.Text, nullable=True)
    comentarios = db.Column(db.Text, nullable=True)

    # Imagen individual de sentimiento / métricas
    imagen_metrica = db.Column(db.String(255), nullable=True)

    # Relación a múltiples imágenes de campaña
    imagenes = db.relationship(
        "CampanaImagen", backref="campana", cascade="all, delete-orphan"
    )


# 4. TABLA PARA MÚLTIPLES IMÁGENES DE CAMPAÑA (1:N)
class CampanaImagen(db.Model):
    __tablename__ = "campana_imagenes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campana_id = db.Column(
        db.Integer,
        db.ForeignKey("seguimiento_campanas.id", ondelete="CASCADE"),
        nullable=False,
    )

    ruta_imagen = db.Column(
        db.String(255), nullable=False
    )  # P. ej. 'assets/uploads/campana_1_img2.jpg'
    nombre_original = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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


def guardar_imagen(archivo):
    """Guarda una imagen y devuelve la ruta relativa que se persiste en la DB."""
    if not archivo or not archivo.filename or not allowed_file(archivo.filename):
        return None

    nombre_original = secure_filename(archivo.filename)
    extension = os.path.splitext(nombre_original)[1].lower()
    nombre_unico = f"{uuid.uuid4().hex}{extension}"
    archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_unico))
    return os.path.join('uploads', nombre_unico), nombre_original


def hay_datos_campana(analisis, comentarios, imagenes, imagen_metrica, no_hubo):
    return bool(
        no_hubo
        or (analisis and analisis.strip())
        or (comentarios and comentarios.strip())
        or any(archivo and archivo.filename for archivo in imagenes)
        or any(archivo and archivo.filename for archivo in imagen_metrica)
    )



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
        apellido = request.form.get("apellido")
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
                apellido=apellido,
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
@app.route("/reportes",  methods=["GET", "POST"])
@login_required
def reportes():
    if request.method == "POST":
        archivos_guardados = []
        try:
            escenarios = json.loads(request.form.get("escenarios_json", "[]"))
            if not isinstance(escenarios, list):
                raise ValueError("El formato de escenarios no es válido.")

            reporte = ReporteCompetencia(
                estado=EstadoReporte.PENDIENTE,
                tipo_reporte=request.form.get("tipo_reporte") or "competencia",
                situacion_movistar=request.form.get("situacion_movistar", "").strip(),
                situacion_digitel=request.form.get("situacion_digitel", "").strip(),
            )
            db.session.add(reporte)

            for escenario in escenarios:
                if not isinstance(escenario, dict):
                    raise ValueError("Uno de los escenarios no es válido.")
                categoria = str(escenario.get("categoria", "")).strip().upper()
                if categoria not in EscenarioCategoria.__members__:
                    raise ValueError(f"Categoría de escenario inválida: {categoria}")
                reporte.escenarios.append(EscenarioAccion(
                    categoria=EscenarioCategoria[categoria],
                    analisis=str(escenario.get("analisis", "")).strip(),
                    curso_accion=str(escenario.get("curso_accion", "")).strip(),
                ))

            campanas = (
                ("Movistar", "movistar"),
                ("Digitel", "digitel"),
            )
            for operadora, clave in campanas:
                no_hubo = request.form.get(f"no_campana_{clave}") == "1"
                imagenes = request.files.getlist(f"campana_{clave}_imagenes")
                imagen_metrica = request.files.getlist(f"campana_{clave}_metrica_imagen")
                analisis = request.form.get(f"campana_{clave}_analisis", "").strip()
                comentarios = request.form.get(f"campana_{clave}_comentarios", "").strip()

                if not hay_datos_campana(analisis, comentarios, imagenes, imagen_metrica, no_hubo):
                    continue

                seguimiento = SeguimientoCampana(
                    operadora=operadora,
                    analisis=analisis,
                    comentarios=comentarios,
                )
                reporte.seguimientos.append(seguimiento)

                for archivo in imagenes:
                    resultado = guardar_imagen(archivo)
                    if resultado:
                        ruta, nombre_original = resultado
                        archivos_guardados.append(os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(ruta)))
                        seguimiento.imagenes.append(CampanaImagen(
                            ruta_imagen=ruta,
                            nombre_original=nombre_original,
                        ))

                for archivo in imagen_metrica:
                    resultado = guardar_imagen(archivo)
                    if resultado:
                        ruta, _ = resultado
                        archivos_guardados.append(os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(ruta)))
                        seguimiento.imagen_metrica = ruta
                        break

            db.session.commit()
            flash("Reporte guardado y enviado a revisión.", "success")
        except (ValueError, json.JSONDecodeError) as error:
            db.session.rollback()
            for ruta in archivos_guardados:
                if os.path.exists(ruta):
                    os.remove(ruta)
            flash(str(error), "error")
        except (SQLAlchemyError, OSError):
            db.session.rollback()
            for ruta in archivos_guardados:
                if os.path.exists(ruta):
                    os.remove(ruta)
            flash("No se pudo guardar el reporte.", "error")

        return redirect(url_for("reportes"))

    return render_template("reportes.html")


if __name__ == '__main__':
    app.run(debug=True)