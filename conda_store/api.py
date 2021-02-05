import logging
import math
import datetime

from sqlalchemy import and_

from conda_store import orm, environment


logger = logging.getLogger(__name__)


def list_environments(db):
    return db.query(orm.Environment).all()


def get_environment(db, name):
    return db.query(orm.Environment).filter(
        orm.Environment.name == name
    ).first()


def get_environment_builds(db, name):
    return db.query(orm.Build).filter(
        orm.Build.specification.name == name
    ).all()


def get_specification(db, sha256):
    return db.query(orm.Specification).filter(
        orm.Specification.sha256 == sha256
    ).first()


def post_specification(conda_store, specification):
    conda_store.register_environment(specification, namespace='library')


def get_build(db, build_id):
    return db.query(orm.Build).filter(
        orm.Build.id == build_id
    ).first()


def get_num_queued_builds(db):
    return db.query(orm.Build).filter(
        orm.Build.status == orm.BuildStatus.QUEUED
    ).count()


def get_num_schedulable_builds(db):
    return db.query(orm.Build).filter(and_(
        orm.Build.status == orm.BuildStatus.QUEUED,
        orm.Build.scheduled_on < datetime.datetime.utcnow()
    )).count()


def get_build_lockfile(db, build_id):
    build = db.query(orm.Build).filter(orm.Build.id == build_id).first()
    packages = [f'{row.channel}/{row.subdir}/{row.name}-{row.version}-{row.build}.tar.bz2#{row.md5}' for row in build.packages]
    return '''#platform: linux-64
@EXPLICIT
{0}
'''.format('\n'.join(packages))


def get_build_docker_archive(db, storage, build_id):
    pass


def list_conda_packages(db, limit=10):
    query = db.query(
        orm.CondaPackage.channel,
        orm.CondaPackage.build,
        orm.CondaPackage.build_number,
        orm.CondaPackage.constrains,
        orm.CondaPackage.depends,
        orm.CondaPackage.license,
        orm.CondaPackage.license_family,
        orm.CondaPackage.md5,
        orm.CondaPackage.name,
        orm.CondaPackage.sha256,
        orm.CondaPackage.size,
        orm.CondaPackage.subdir,
        orm.CondaPackage.timestamp,
        orm.CondaPackage.version).limit(limit)
    return [row._asdict() for row in query.all()]


def get_metrics(db):
    metrics = db.query(
        orm.CondaStoreConfiguration.free_storage.label('free'),
        orm.CondaStoreConfiguration.total_storage.label('total'),
        orm.CondaStoreConfiguration.disk_usage).first()._asdict()

    metrics['total_completed_builds'] = db.query(orm.Build).filter(
        orm.Build.status == orm.BuildStatus.COMPLETED).count()
    metrics['total_environments'] = db.query(orm.Environment).count()
    metrics['used'] = metrics['total'] - metrics['free']
    metrics['percent'] = math.ceil(metrics['used'] / metrics['total'] * 100)
    return metrics
