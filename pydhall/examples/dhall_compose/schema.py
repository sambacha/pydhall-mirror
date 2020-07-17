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
    network    = TextField(optional="omitNone", default=None)
    target     = TextField(optional="omitNone", default=None)
    args       = UnionField(ListOrMap, default={"List": []})
    labels     = UnionField(ListOrMap, default={"List": []})
    cache_from = ListOfField(Text, optional="omitNone", default=None)
    shm_size   = UnionField(StringOrNatural, optional="omitNone", default=None)


class Build(Union):
    BuildDir = Alt(Text)
    Build = Alt(BuildConfig)


# services.*.config

class LongConfig(Record):
    source = TextField(optional="omitNone")
    target = TextField(optional="omitNone")
    uid = TextField(optional="omitNone", default="'0'")
    gid = TextField(optional="omitNone", default="'0'")
    mode = NaturalField(optional="omitNone", default=292)


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
    aliases = ListOfField(Text, optional="omitNone")
    ipv4_address = TextField(optional="omitNone")
    ipv6_address = TextField(optional="omitNone")


class Networks(Union):
    Refs = Alt(ListOf("_anonList", Text))
    Defs = Alt(MapOf("_anonMap", ServiceNetworkDef))


# services.*.ports

class PortDef(Record):
    mode = TextField(optional="omitNone")
    target = NaturalField(optional="omitNone")
    published = NaturalField(optional="omitNone")
    protocol = TextField(optional="omitNone")


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
    image             = TextField(optional="omitNone", default=None)
    build             = UnionField(Build, optional="omitNone", default=None)
    cap_add           = ListOfField(Text, optional="omitNone", default=None)
    cap_drop          = ListOfField(Text, optional="omitNone", default=None)
    cgroup_parent     = TextField(optional="omitNone", default=None)
    command           = UnionField(StringOrList, optional="omitNone", default=None)
    configs           = UnionField(ServiceConfig, optional="omitNone", default=None)
    container_name    = TextField(optional="omitNone", default=None)
    # credential_spec = RecordField(...)  # TODO: MS Windows only
    depends_on        = ListOfField(Text, optional="omitNone", default=None)
    # deploy          = RecordField(...)  # TODO: swarm only
    devices           = ListOfField(Text, optional="omitNone", default=None)
    dns               = UnionField(StringOrList, optional="omitNone", default=None)
    dns_search        = UnionField(StringOrList, optional="omitNone", default=None)
    domain_name       = TextField(optional="omitNone", default=None)
    entrypoint        = UnionField(StringOrList, optional="omitNone", default=None)
    env_file          = UnionField(StringOrList, optional="omitNone", default=None)
    environment       = UnionField(ListOrMap, default={"List": []})
    expose            = ListOfField(Natural, optional="omitNone", default=None)
    extra_hosts       = UnionField(ListOrMap, optional="omitNone", default=None)
    healtcheck        = RecordField(Healthcheck, optional="omitNone", default=None)
    hostname          = TextField(optional="omitNone", default=None)
    init              = BoolField(default=False)
    ipc               = TextField(default="")
    isolation         = TextField(default="default")
    labels            = UnionField(ListOrMap, optional="omitNone", default=None)
    logging           = RecordField(Logging, optional="omitNone", default=None)
    mac_address       = TextField(optional="omitNone", default=None)
    # TODO: ChoiceField
    network_mode      = TextField(optional="omitNone", default=None)
    networks          = UnionField(Networks, optional="omitNone", default=None)
    pid               = TextField(optional="omitNone", default=None)
    ports             = ListOfField(Port, default=[])
    privileged        = BoolField(optional="omitNone", default=None)
    read_only         = BoolField(optional="omitNone", default=None)
    restart           = TextField(optional="omitNone", default=None)
    security_opt      = ListOfField(Text, optional="omitNone", default=None)
    shm_size          = TextField(optional="omitNone", default=None)
    # secrets         = ...  # TODO.
    sysctl            = UnionField(ListOrMap, optional="omitNone", default=None)
    stdin_open        = BoolField(optional="omitNone", default=None)
    stop_grace_period = TextField(optional="omitNone", default=None)
    stop_signal       = TextField(optional="omitNone", default=None)
    tmpfs             = UnionField(StringOrList, optional="omitNone", default=None)
    tty               = BoolField(optional="omitNone", default=None)
    ulimits           = MapOfField(Ulimit, optional="omitNone", default=None)
    user              = TextField(optional="omitNone", default=None)
    userns_mode       = TextField(optional="omitNone", default=None)
    volumes           = ListOfField(ServiceVolume, optional="omitNone", default=None)
    working_dir       = TextField(optional="omitNone", default=None)


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
