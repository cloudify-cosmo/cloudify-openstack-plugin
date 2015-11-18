import copy
import errno
import fcntl
import itertools
import json
import os
import stat

import cloudify


_DBFILE_FORMATSTR = '~/cloudify.openstack.{0}.{1}'
_LOCK_RETRY_TIME = 1


def retreive_related_node_instances(node_type, root=None):
    if root is None:
        root = cloudify.ctx.instance
    related = []
    for r in root.relationships:
        t = r.target
        t.node._get_node_if_needed()
        if node_type in t.node._node.type_hierarchy:
            related.append(t.instance)
    return related


def retreive_grouped_related_node_instances(node_type, root=None):
    ig = {}
    try:
        if root is None:
            root = cloudify.ctx.instance
        for r in root.relationships:
            t = r.target
            t.node._get_node_if_needed()
            if node_type not in t.node._node.type_hierarchy:
                continue
            i = ig.get(t.node.id, [])
            i.append(t.instance.id)
            ig[t.node.id] = i
    except Exception as e:
        raise cloudify.exceptions.NonRecoverableError(e)
    return ig.values()


def cfyid2osid(cfy_ids):
    if not cfy_ids:
        return []
    cfy_ids = copy.deepcopy(cfy_ids)
    os_ids = []
    try:
        for r in cloudify.ctx.instance.relationships:
            t = r.target
            if t.instance.id in cfy_ids:
                os_ids.append(t.instance.runtime_properties['external_id'])
                cfy_ids.remove(t.instance.id)
                if not cfy_ids:
                    break
    except Exception as e:
        raise cloudify.exceptions.NonRecoverableError(e)
    return os_ids


def simulate_relationship_one2one_or_retry():
    dbfile = os.path.expanduser(
        _DBFILE_FORMATSTR.format(cloudify.ctx.deployment.id,
                                 cloudify.ctx.target.node.id)
    )
    try:
        fd = None
        try:
            fd = os.open(dbfile,
                         os.O_RDWR | os.O_CREAT,
                         stat.S_IRUSR | stat.S_IWUSR)
            f = os.fdopen(fd, 'r+')
            try:
                fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError as e:
                if e.errno == errno.EAGAIN or e.errno == errno.EACCES:
                    return (cloudify.ctx.operation.retry('locked',
                                                         _LOCK_RETRY_TIME),
                            None)
                raise
            try:
                dbraw = f.read()
                db = json.loads(dbraw) if dbraw else {}
                src = db.get(cloudify.ctx.source.instance.id)
                tgt = db.get(cloudify.ctx.target.instance.id)
                if (src and tgt and
                        src == cloudify.ctx.target.instance.id and
                        tgt == cloudify.ctx.source.instance.id):
                    return None, True
                elif not src and not tgt:
                    db[cloudify.ctx.source.instance.id] = \
                        cloudify.ctx.target.instance.id
                    db[cloudify.ctx.target.instance.id] = \
                        cloudify.ctx.source.instance.id
                    f.seek(0)
                    json.dump(db, f)
                    f.flush()
                    return None, True
                else:
                    return None, False
            finally:
                fcntl.lockf(f, fcntl.LOCK_UN)
        finally:
            if fd is not None:
                f.close()
    except cloudify.exceptions.NonRecoverableError:
        raise
    except Exception as e:
        raise cloudify.exceptions.NonRecoverableError(e)


def simulate_node_one2one_or_retry(instances_grouped):
    dbfile = os.path.expanduser(
        _DBFILE_FORMATSTR.format(cloudify.ctx.deployment.id,
                                 cloudify.ctx.node.id)
    )
    try:
        fd = None
        try:
            fd = os.open(dbfile,
                         os.O_RDONLY | os.O_CREAT,
                         stat.S_IRUSR | stat.S_IWUSR)
            f = os.fdopen(fd, 'r')
            try:
                fcntl.lockf(f, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except IOError as e:
                if e.errno == errno.EAGAIN or e.errno == errno.EACCES:
                    return (cloudify.ctx.operation.retry('locked',
                                                         _LOCK_RETRY_TIME),
                            None)
                raise
            try:
                dbraw = f.read()
            finally:
                fcntl.lockf(f, fcntl.LOCK_UN)
        finally:
            if fd is not None:
                f.close()
        db = json.loads(dbraw) if dbraw else {}
        connections = db.get(cloudify.ctx.instance.id)
        if connections is None:
            connections = []
            fd = None
            try:
                fd = os.open(dbfile, os.O_RDWR)
                f = os.fdopen(fd, 'r+')
                try:
                    fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except IOError as e:
                    if e.errno == errno.EAGAIN or e.errno == errno.EACCES:
                        return (cloudify.ctx.operation.retry('locked',
                                                             _LOCK_RETRY_TIME),
                                None)
                    raise
                try:
                    dbraw = f.read()
                    db = json.loads(dbraw) if dbraw else {}
                    dbflat = list(itertools.chain(*db.itervalues()))
                    for g in instances_grouped:
                        for i in g:
                            if i not in dbflat:
                                connections.append(i)
                                dbflat.append(i)
                                break
                        else:
                            raise cloudify.exceptions.NonRecoverableError(
                                'connection number mismatch'
                            )
                    db[cloudify.ctx.instance.id] = connections
                    f.seek(0)
                    json.dump(db, f)
                    f.flush()
                finally:
                    fcntl.lockf(f, fcntl.LOCK_UN)
            finally:
                if fd is not None:
                    f.close()
    except cloudify.exceptions.NonRecoverableError:
        raise
    except Exception as e:
        raise cloudify.exceptions.NonRecoverableError(e)
    return None, connections
