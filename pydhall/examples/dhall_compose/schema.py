from pydhall.schema import *
from pydhall.schema.render import render
from yaml import safe_dump

# misc

class StringOrList(Union):
    List = Alt(ListOf("_anonList", Text))
    String = Alt(Text)


class ListOrMap(Union):
    List = Alt(ListOf("_anonList", Text))
    Map = Alt(MapOf("_anonMap", Text))


class StringOrNatural(Union):
    Natural = Alt(Natural)
    String = Alt(Text)


class MapItem(Union):
    String = Alt(Text)
    Number = Alt(Natural)
    Null = Alt()


# services.*.build

class BuildConfig(Record):
    context    = TextField(default=".")
    dockerfile = TextField(default="Dockerfile")
    network    = TextField(optional="ommitNone", default=None)
    target     = TextField(optional="ommitNone", default=None)
    args       = UnionField(ListOrMap, default={"List": []})
    labels     = UnionField(ListOrMap, default={"List": []})
    cache_from = ListOfField(Text, optional="ommitNone", default=None)
    shm_size   = UnionField(StringOrNatural, optional="ommitNone", default=None)


class Build(Union):
    BuildDir = Alt(Text)
    Build = Alt(BuildConfig)


# services.*.config

class LongConfig(Record):
    source = TextField(optional="ommitNone")
    target = TextField(optional="ommitNone")
    uid = TextField(optional="ommitNone", default="'0'")
    gid = TextField(optional="ommitNone", default="'0'")
    mode = NaturalField(optional="ommitNone", default=292)


class ServiceConfig(Union):
    Ref = Alt(Text)
    Def = Alt(LongConfig)


# services.*.healthcheck

class Healthcheck(Record):
    disable = BoolField(default=False)
    interval = TextField(default="30s")
    retries = NaturalField(default=3)
    test = UnionField(StringOrList)
    timeout = TextField(default="30s")
    start_period = TextField(default="0s")


# services.*.logging

class Logging(Record):
    driver = TextField()
    options = MapOfField(MapItem)


# services.*.networks

class ServiceNetworkDef(Record):
    aliases = ListOfField(Text, optional="ommitNone")
    ipv4_address = TextField(optional="ommitNone")
    ipv6_address = TextField(optional="ommitNone")


class Networks(Union):
    Refs = Alt(ListOf("_anonList", Text))
    Defs = Alt(MapOf("_anonMap", ServiceNetworkDef))


# services.*.ports

class PortDef(Record):
    mode = TextField(optional="ommitNone")
    target = NaturalField(optional="ommitNone")
    published = NaturalField(optional="ommitNone")
    protocol = TextField(optional="ommitNone")


class Port(Union):
    Text = Alt(Text)
    Def = Alt(PortDef)


# services.*.ulimits

class UlimitDef(Record):
    hard = NaturalField()
    soft = NaturalField()


class Ulimit(Union):
    Natural = Alt(Natural)
    Def = Alt(UlimitDef)

# services.*.volumes

class VolumeBind(Record):
    propagation = TextField()


class VolumeVolume(Record):
    nocopy = BoolField()


class VolumeTmpfs(Record):
    size = NaturalField()


class VolumeDef(Record):
    type        = TextField()
    source      = TextField()
    target      = TextField()
    read_only   = BoolField()
    consistency = TextField()
    bind        = RecordField(VolumeBind)
    volume      = RecordField(VolumeVolume)
    tmpfs       = RecordField(VolumeTmpfs)


class ServiceVolume(Union):
    Ref = Alt(Text)
    Def = Alt(VolumeDef)

# services.*

class Service(Record):
    image             = TextField(optional="ommitNone", default=None)
    build             = UnionField(Build, optional="ommitNone", default=None)
    cap_add           = ListOfField(Text, optional="ommitNone", default=None)
    cap_drop          = ListOfField(Text, optional="ommitNone", default=None)
    cgroup_parent     = TextField(optional="ommitNone", default=None)
    command           = UnionField(StringOrList, optional="ommitNone", default=None)
    configs           = UnionField(ServiceConfig, optional="ommitNone", default=None)
    container_name    = TextField(optional="ommitNone", default=None)
    # credential_spec = RecordField(...)  # TODO: MS Windows only
    depends_on        = ListOfField(Text, optional="ommitNone", default=None)
    # deploy          = RecordField(...)  # TODO: swarm only
    devices           = ListOfField(Text, optional="ommitNone", default=None)
    dns               = UnionField(StringOrList, optional="ommitNone", default=None)
    dns_search        = UnionField(StringOrList, optional="ommitNone", default=None)
    domain_name       = TextField(optional="ommitNone", default=None)
    entrypoint        = UnionField(StringOrList, optional="ommitNone", default=None)
    env_file          = UnionField(StringOrList, optional="ommitNone", default=None)
    environment       = UnionField(ListOrMap, default={"List": []})
    expose            = ListOfField(Natural, optional="ommitNone", default=None)
    extra_hosts       = UnionField(ListOrMap, optional="ommitNone", default=None)
    healtcheck        = RecordField(Healthcheck, optional="ommitNone", default=None)
    hostname          = TextField(optional="ommitNone", default=None)
    init              = BoolField(default=False)
    ipc               = TextField(default="")
    isolation         = TextField(default="default")
    labels            = UnionField(ListOrMap, optional="ommitNone", default=None)
    logging           = RecordField(Logging, optional="ommitNone", default=None)
    mac_address       = TextField(optional="ommitNone", default=None)
    # TODO: ChoiceField
    network_mode      = TextField(optional="ommitNone", default=None)
    networks          = UnionField(Networks, optional="ommitNone", default=None)
    pid               = TextField(optional="ommitNone", default=None)
    ports             = ListOfField(Port, default=[])
    privileged        = BoolField(optional="ommitNone", default=None)
    read_only         = BoolField(optional="ommitNone", default=None)
    restart           = TextField(optional="ommitNone", default=None)
    security_opt      = ListOfField(Text, optional="ommitNone", default=None)
    shm_size          = TextField(optional="ommitNone", default=None)
    # secrets         = ...  # TODO.
    sysctl            = UnionField(ListOrMap, optional="ommitNone", default=None)
    stdin_open        = BoolField(optional="ommitNone", default=None)
    stop_grace_period = TextField(optional="ommitNone", default=None)
    stop_signal       = TextField(optional="ommitNone", default=None)
    tmpfs             = UnionField(StringOrList, optional="ommitNone", default=None)
    tty               = BoolField(optional="ommitNone", default=None)
    ulimits           = MapOfField(Ulimit, optional="ommitNone", default=None)
    user              = TextField(optional="ommitNone", default=None)
    userns_mode       = TextField(optional="ommitNone", default=None)
    volumes           = ListOfField(ServiceVolume, optional="ommitNone", default=None)
    working_dir       = TextField(optional="ommitNone", default=None)


class Compose(Record):
    version = TextField(default="3.8")
    services = MapOfField(Service)


if __name__ == "__main__":
    import sys
    try:
        compose_file = sys.argv[1]
    except IndexError:
        compose_file = "./docker-compose.dhall"
    with open(compose_file) as f:
        cfg = load_src(Compose, f.read())
    # print(render(cfg))
    # import ipdb; ipdb.set_trace()
    safe_dump(render(cfg),sys.stdout)
