import os
import json
import uuid
from io import BytesIO
from flask import Flask, render_template, render_template_string, redirect, request, url_for, flash, send_file
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
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

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


#  TABLA PARA MÚLTIPLES IMÁGENES DE CAMPAÑA (1:N)
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

            situacion_movistar = request.form.get("situacion_movistar", "").strip()
            situacion_digitel = request.form.get("situacion_digitel", "").strip()
            escenarios_validos = []
            for escenario in escenarios:
                if not isinstance(escenario, dict):
                    raise ValueError("Uno de los escenarios no es válido.")

                categoria = str(escenario.get("categoria", "")).strip().upper()
                analisis = str(escenario.get("analisis", "")).strip()
                curso_accion = str(escenario.get("curso_accion", "")).strip()
                if categoria not in EscenarioCategoria.__members__:
                    raise ValueError(f"Categoría de escenario inválida: {categoria}")
                if not analisis or not curso_accion:
                    raise ValueError("Cada escenario debe tener análisis y curso de acción.")
                escenarios_validos.append((categoria, analisis, curso_accion))

            hay_datos_campanas = False
            for _, clave in (("Movistar", "movistar"), ("Digitel", "digitel")):
                hay_datos_campanas = hay_datos_campanas or hay_datos_campana(
                    request.form.get(f"campana_{clave}_analisis", "").strip(),
                    request.form.get(f"campana_{clave}_comentarios", "").strip(),
                    request.files.getlist(f"campana_{clave}_imagenes"),
                    request.files.getlist(f"campana_{clave}_metrica_imagen"),
                    request.form.get(f"no_campana_{clave}") == "1",
                )

            if not (situacion_movistar or situacion_digitel or escenarios_validos or hay_datos_campanas):
                raise ValueError("No se puede guardar un reporte vacío. Completa al menos un campo.")

            reporte = ReporteCompetencia(
                estado=EstadoReporte.PENDIENTE,
                tipo_reporte=request.form.get("tipo_reporte") or "competencia",
                situacion_movistar=situacion_movistar,
                situacion_digitel=situacion_digitel,
            )
            db.session.add(reporte)

            for categoria, analisis, curso_accion in escenarios_validos:
                reporte.escenarios.append(EscenarioAccion(
                    categoria=EscenarioCategoria[categoria],
                    analisis=analisis,
                    curso_accion=curso_accion,
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

        return redirect(url_for("dashboard"))

    return render_template("reportes.html")

@app.route("/dashboard")
@login_required
def dashboard():
    reportes = ReporteCompetencia.query.order_by(ReporteCompetencia.updated_at.desc()).all()
    return render_template("dashboard.html", reportes=reportes)


@app.route("/reportes/<int:reporte_id>/editar", methods=["GET", "POST"])
@requiere_rol("Admin")
def editar_reporte(reporte_id):
    reporte = ReporteCompetencia.query.get_or_404(reporte_id)
    if reporte.estado not in (EstadoReporte.BORRADOR, EstadoReporte.PENDIENTE):
        flash("Este reporte no puede editarse en su estado actual.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        try:
            escenarios = json.loads(request.form.get("escenarios_json", "[]"))
            if not isinstance(escenarios, list):
                raise ValueError("El formato de escenarios no es válido.")

            imagenes_eliminadas = []
            ids_imagenes = request.form.getlist("eliminar_imagenes")
            if ids_imagenes:
                imagenes = CampanaImagen.query.filter(
                    CampanaImagen.id.in_(ids_imagenes)
                ).all()
                if len(imagenes) != len(set(ids_imagenes)) or any(
                    imagen.campana.reporte_id != reporte.id for imagen in imagenes
                ):
                    raise ValueError("Una de las imágenes seleccionadas no pertenece al reporte.")
                for imagen in imagenes:
                    imagenes_eliminadas.append(imagen.ruta_imagen)
                    db.session.delete(imagen)

            reporte.tipo_reporte = request.form.get("tipo_reporte", "competencia").strip()
            reporte.situacion_movistar = request.form.get("situacion_movistar", "").strip()
            reporte.situacion_digitel = request.form.get("situacion_digitel", "").strip()
            reporte.escenarios.clear()

            for escenario in escenarios:
                categoria = str(escenario.get("categoria", "")).strip().upper()
                if categoria not in EscenarioCategoria.__members__:
                    raise ValueError(f"Categoría de escenario inválida: {categoria}")
                reporte.escenarios.append(EscenarioAccion(
                    categoria=EscenarioCategoria[categoria],
                    analisis=str(escenario.get("analisis", "")).strip(),
                    curso_accion=str(escenario.get("curso_accion", "")).strip(),
                ))

            for operadora, clave in (("Movistar", "movistar"), ("Digitel", "digitel")):
                seguimiento = next((item for item in reporte.seguimientos if item.operadora == operadora), None)
                if seguimiento is None:
                    seguimiento = SeguimientoCampana(operadora=operadora)
                    reporte.seguimientos.append(seguimiento)

                if request.form.get(f"eliminar_metrica_{clave}") == "1":
                    if seguimiento.imagen_metrica:
                        imagenes_eliminadas.append(seguimiento.imagen_metrica)
                    seguimiento.imagen_metrica = None

                seguimiento.analisis = request.form.get(f"campana_{clave}_analisis", "").strip()
                seguimiento.comentarios = request.form.get(f"campana_{clave}_comentarios", "").strip()

                for archivo in request.files.getlist(f"campana_{clave}_imagenes"):
                    resultado = guardar_imagen(archivo)
                    if resultado:
                        ruta, nombre_original = resultado
                        seguimiento.imagenes.append(CampanaImagen(
                            ruta_imagen=ruta,
                            nombre_original=nombre_original,
                        ))
                for archivo in request.files.getlist(f"campana_{clave}_metrica_imagen"):
                    resultado = guardar_imagen(archivo)
                    if resultado:
                        seguimiento.imagen_metrica = resultado[0]
                        break

            reporte.estado = EstadoReporte.BORRADOR
            reporte.updated_at = datetime.utcnow()
            db.session.commit()
            for ruta in imagenes_eliminadas:
                ruta_archivo = os.path.join(app.config["UPLOAD_FOLDER"], os.path.basename(ruta))
                if os.path.exists(ruta_archivo):
                    os.remove(ruta_archivo)
            flash("Los cambios del borrador se guardaron correctamente.", "success")
            return redirect(url_for("dashboard"))
        except (ValueError, json.JSONDecodeError, SQLAlchemyError, OSError) as error:
            db.session.rollback()
            flash(str(error) if isinstance(error, ValueError) else "No se pudo guardar la edición del reporte.", "error")

    seguimientos = {item.operadora.lower(): item for item in reporte.seguimientos}
    return render_template("editar_reporte.html", reporte=reporte, seguimientos=seguimientos, guardado=request.args.get("guardado") == "1")


def _agregar_texto(slide, texto, left, top, width, height, font_size=18, color=(31, 31, 31), bold=False):
    caja = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    marco = caja.text_frame
    marco.clear()
    marco.word_wrap = True
    for indice, parrafo_texto in enumerate(str(texto or "Sin información.").split("\n")):
        parrafo = marco.paragraphs[0] if indice == 0 else marco.add_paragraph()
        parrafo.text = parrafo_texto
        parrafo.font.name = "Aptos"
        parrafo.font.size = Pt(font_size)
        parrafo.font.bold = bold
        parrafo.font.color.rgb = RGBColor(*color)
        parrafo.space_after = Pt(6)
    return caja


def _estilo_slide(slide, titulo, subtitulo=None):
    fondo = slide.background.fill
    fondo.solid()
    fondo.fore_color.rgb = RGBColor(244, 244, 244)
    banda = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(0.22))
    banda.fill.solid()
    banda.fill.fore_color.rgb = RGBColor(201, 59, 59)
    banda.line.fill.background()
    _agregar_texto(slide, titulo, 0.65, 0.55, 12, 0.55, 26, (201, 59, 59), True)
    if subtitulo:
        _agregar_texto(slide, subtitulo, 0.65, 1.12, 12, 0.3, 10, (115, 115, 115))


def generar_pptx(reporte):
    presentacion = Presentation()
    presentacion.slide_width = Inches(13.333)
    presentacion.slide_height = Inches(7.5)
    layout = presentacion.slide_layouts[6]

    portada = presentacion.slides.add_slide(layout)
    _estilo_slide(portada, "Análisis de la competencia", "Movilnet Intelligence")
    _agregar_texto(portada, f"Reporte #{reporte.id}", 0.8, 2.35, 11.8, 0.8, 34, (31, 31, 31), True)
    _agregar_texto(portada, f"Tipo: {reporte.tipo_reporte.capitalize()}\nActualizado: {reporte.updated_at.strftime('%d/%m/%Y %H:%M')}", 0.85, 3.35, 5.5, 1.0, 16, (115, 115, 115))
    _agregar_texto(portada, "Inteligencia competitiva", 0.85, 6.55, 5, 0.3, 11, (201, 59, 59), True)

    situacion = presentacion.slides.add_slide(layout)
    _estilo_slide(situacion, "Situación actual", "Lectura comparativa de operadores")
    for left, nombre, contenido in ((0.7, "Movistar", reporte.situacion_movistar), (6.85, "Digitel", reporte.situacion_digitel)):
        panel = situacion.shapes.add_shape(5, Inches(left), Inches(1.75), Inches(5.75), Inches(4.7))
        panel.fill.solid()
        panel.fill.fore_color.rgb = RGBColor(255, 255, 255)
        panel.line.color.rgb = RGBColor(229, 229, 229)
        _agregar_texto(situacion, nombre, left + 0.3, 2.05, 5.1, 0.4, 20, (201, 59, 59), True)
        _agregar_texto(situacion, contenido, left + 0.3, 2.65, 5.1, 3.3, 15)

    for indice, escenario in enumerate(reporte.escenarios, 1):
        slide = presentacion.slides.add_slide(layout)
        _estilo_slide(slide, f"Escenario {indice}: {escenario.categoria.value}", "Análisis y curso de acción estratégico")
        _agregar_texto(slide, "ANÁLISIS", 0.8, 1.85, 5.8, 0.3, 11, (201, 59, 59), True)
        _agregar_texto(slide, escenario.analisis, 0.8, 2.25, 5.7, 3.8, 17)
        _agregar_texto(slide, "CURSO DE ACCIÓN", 6.95, 1.85, 5.5, 0.3, 11, (201, 59, 59), True)
        _agregar_texto(slide, escenario.curso_accion, 6.95, 2.25, 5.55, 3.8, 17)

    for seguimiento in reporte.seguimientos:
        slide = presentacion.slides.add_slide(layout)
        _estilo_slide(slide, f"Seguimiento de campaña: {seguimiento.operadora}", "Campañas, percepción y métricas")
        _agregar_texto(slide, "ANÁLISIS DE CAMPAÑA", 0.8, 1.8, 5.7, 0.3, 11, (201, 59, 59), True)
        _agregar_texto(slide, seguimiento.analisis, 0.8, 2.2, 5.7, 1.8, 15)
        _agregar_texto(slide, "COMENTARIOS DE USUARIOS", 0.8, 4.25, 5.7, 0.3, 11, (201, 59, 59), True)
        _agregar_texto(slide, seguimiento.comentarios, 0.8, 4.65, 5.7, 1.3, 15)
        ruta_metrica = os.path.join(app.config["UPLOAD_FOLDER"], os.path.basename(seguimiento.imagen_metrica or ""))
        if seguimiento.imagen_metrica and os.path.exists(ruta_metrica):
            slide.shapes.add_picture(ruta_metrica, Inches(7.1), Inches(2.0), width=Inches(5.3), height=Inches(3.8))

    salida = BytesIO()
    presentacion.save(salida)
    salida.seek(0)
    return salida


@app.route("/reportes/<int:reporte_id>/presentacion")
@login_required
def crear_presentacion(reporte_id):
    reporte = ReporteCompetencia.query.get_or_404(reporte_id)
    return render_template("presentacion.html", reporte=reporte)


@app.route("/reportes/<int:reporte_id>/presentacion/pptx")
@login_required
def descargar_presentacion(reporte_id):
    reporte = ReporteCompetencia.query.get_or_404(reporte_id)
    archivo = generar_pptx(reporte)
    return send_file(
        archivo,
        as_attachment=True,
        download_name=f"analisis_competencia_reporte_{reporte.id}.pptx",
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


if __name__ == '__main__':
    app.run(debug=True)