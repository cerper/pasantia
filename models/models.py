import enum
from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

roles_usuarios = db.Table(
    "roles_usuarios",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("role_id", db.Integer, db.ForeignKey("role.id")),
)


class Role(db.Model):
    __tablename__ = "role"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True)


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)
    roles = db.relationship(
        "Role",
        secondary=roles_usuarios,
        backref=db.backref("usuarios", lazy="dynamic"),
    )

    def tiene_rol(self, nombre_rol):
        return any(role.nombre == nombre_rol for role in self.roles)


class EstadoReporte(enum.Enum):
    BORRADOR = "Borrador"
    PENDIENTE = "Pendiente"
    APROBADO = "Aprobado"


class EscenarioCategoria(enum.Enum):
    NEUTRAL = "Neutral"
    FAVORABLE = "Favorable"
    DESFAVORABLE = "Desfavorable"


class ReporteCompetencia(db.Model):
    __tablename__ = "reportes_competencia"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    estado = db.Column(
        db.Enum(EstadoReporte),
        nullable=False,
        default=EstadoReporte.BORRADOR,
        index=True,
    )
    tipo_reporte = db.Column(db.String(50), nullable=False, default="competencia")
    situacion_movistar = db.Column(db.Text, nullable=True)
    situacion_digitel = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    escenarios = db.relationship(
        "EscenarioAccion", backref="reporte", cascade="all, delete-orphan"
    )
    seguimientos = db.relationship(
        "SeguimientoCampana", backref="reporte", cascade="all, delete-orphan"
    )


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


class SeguimientoCampana(db.Model):
    __tablename__ = "seguimiento_campanas"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reporte_id = db.Column(
        db.Integer,
        db.ForeignKey("reportes_competencia.id", ondelete="CASCADE"),
        nullable=False,
    )
    operadora = db.Column(db.String(20), nullable=False)
    analisis = db.Column(db.Text, nullable=True)
    comentarios = db.Column(db.Text, nullable=True)
    imagen_metrica = db.Column(db.String(255), nullable=True)
    imagenes = db.relationship(
        "CampanaImagen", backref="campana", cascade="all, delete-orphan"
    )


class CampanaImagen(db.Model):
    __tablename__ = "campana_imagenes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campana_id = db.Column(
        db.Integer,
        db.ForeignKey("seguimiento_campanas.id", ondelete="CASCADE"),
        nullable=False,
    )
    ruta_imagen = db.Column(db.String(255), nullable=False)
    nombre_original = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
