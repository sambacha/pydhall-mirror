let Bool/show = ../../../../dhall-lang/Prelude/Bool/show.dhall
let Map/empty = ../../../../dhall-lang/Prelude/Map/empty.dhall
let Map/Type = ../../../../dhall-lang/Prelude/Map/Type.dhall
let Map/Entry = ../../../../dhall-lang/Prelude/Map/Entry.dhall
let List/map = ../../../../dhall-lang/Prelude/List/map.dhall
let List/concatMap = ../../../../dhall-lang/Prelude/List/concatMap.dhall

let compose = pydhall+schema:pydhall.examples.dhall_compose.schema::Compose

-- let RoutingProtocol = < HTTP >

let ExternalHost = < Text : Text | Auto >

let EntryPointDef = {
  ,Type = {
    , name : Text
    , ip: Text
    , container_port : Natural
    , host_port : Optional Natural
    }
  , default = {
    , ip = ""
    , host_port = None Natural
    }
  }
  
let ServiceConfig = {
  , Type = {
    , host : Optional ExternalHost
    -- , entrypoint : 
    }
  , default = {
    , host = Some ExternalHost.Auto
    }
  }


let TraefikEntryPointDefs = {
  , Type = {
    , web : EntryPointDef.Type
    }
  , default = {
    , web = EntryPointDef::{
      , name = "web"
      , container_port = 80
      , host_port = Some 80
      }
    }
  }

let TraefikConfig = {
  , Type = ServiceConfig.Type //\\ {
    , entrypoints : TraefikEntryPointDefs.Type
    , version : Text
    }
  , default = ServiceConfig.default /\ {
    , entrypoints = TraefikEntryPointDefs.default
    , version = "v2.1"
    -- , host = External
    }
  }

let BackendConfig = {
  , Type = ServiceConfig.Type //\\ {
    , debug : Bool
    , secret : Text
    , container_port : Optional Natural
    , host_port : Optional Natural
    }
  , default = ServiceConfig.default /\ {
    , debug = True
    , secret = "secret"
    , container_port = Some 8000
    , host_port = None Natural
    }
  }

let DBConfig = {
  , Type = ServiceConfig.Type //\\ {
    , PGVersion : Text
    , container_port: Natural
    , host_port : Optional Natural
    , user : Text
    , password : Text
    , dbName : Text
    }
  , default = ServiceConfig.default /\ {
    , PGVersion = "11.5"
    , container_port = 5432
    , host_port = None Natural
    , user = "postgres"
    , password = "postgres"
    , dbName = "postgres"
    }
  }

let Config = {
  , Type = {
    , backend : Optional BackendConfig.Type
    , db : Optional DBConfig.Type
    , traefik : Optional TraefikConfig.Type
    }
  , default = {
    , backend = None BackendConfig.Type
    , db = None DBConfig.Type
    , traefik = None TraefikConfig.Type
  }
}

let ComposeServicePort = \(ports : {
      , container_port : Optional Natural
      , host_port : Optional Natural
      }) -> merge {
        , Some = \(ph : Natural) ->
          merge {
          , Some = \(pc : Natural) ->
            [compose.Port.Text "${Natural/show ph}:${Natural/show pc}"]
          , None = [] : List compose.Port
          } ports.container_port
        , None = [] : List compose.Port
        } ports.host_port

let mkBackendService = \(globalCfg : Config.Type)
    -> \(serviceCfg : BackendConfig.Type)
    ->
      let pgDSN = merge {
        , Some = \(dbCfg : DBConfig.Type) ->
          "postgresql://${dbCfg.user}:${dbCfg.password}@db:${Natural/show dbCfg.container_port}/${dbCfg.dbName}"
        , None = ""} globalCfg.db
      in
        compose.Service::{
        , build = Some (compose.Build.Build compose.BuildConfig::{
          , context = "./fastapi-realworld-example-app/"
          })
        , ports = ComposeServicePort serviceCfg.{ container_port, host_port }
        , command = Some ( compose.StringOrList.List [
          , "sh"
          , "-c"
          , "alembic upgrade head && uvicorn --host=0.0.0.0 app.main:app"
          ])
        , environment = compose.ListOrMap.Map (toMap {
          , SECRET_KEY = serviceCfg.secret
          , DEBUG = Bool/show serviceCfg.debug
          , DB_CONNECTION = pgDSN
          })
        , init = True
        }

let mkDBService = \(globalCfg : Config.Type)
    -> \(serviceCfg : DBConfig.Type)
    ->
      compose.Service::{
      , image = Some "postgres:${serviceCfg.PGVersion}-alpine"
      , ports = ComposeServicePort {
        , container_port = Some serviceCfg.container_port
        , host_port = serviceCfg.host_port }
      , volumes = Some [
        , compose.ServiceVolume.Ref "./dbdata:/var/lib/postgresql/data:cached"
        ]
      , environment = compose.ListOrMap.Map (toMap {
        , POSTGRES_USER = serviceCfg.user
        , POSTGRES_PASSWORD = serviceCfg.password
        , PGPORT = Natural/show serviceCfg.container_port
        })
      }

  -- traefik:
  --   image: "traefik:v2.1"
  --   command:
  --     - "--api.insecure=true"
  --     - "--providers.docker=true"
  --     - "--providers.docker.exposedbydefault=false"
  --     - "--entrypoints.web.address=:80"
  --     - "--entrypoints.bolt.address=:7687"
  --     - "--log.level=DEBUG"
  --     - "--accesslog=true"
  --   ports:
  --     - "80:80"
  --     - "8080:8080"
  --     - "7687:7687"
  --   volumes:
  --     - "/var/run/docker.sock:/var/run/docker.sock:ro"
  --   networks:
  --     default:
  --       aliases:

let traefikEP2cmdarg = \(def : Map/Entry Text EntryPointDef.Type) ->
  let val = def.mapValue
  in
    "--entrypoints.${val.name}.address=${val.ip}:${Natural/show val.container_port}"
    
let TraefikEntryPointCmdLine = \(defs : TraefikEntryPointDefs.Type) ->
    List/map
      (Map/Entry Text EntryPointDef.Type)
      Text
      traefikEP2cmdarg
      -- the annotation is mandatory because of a bug in pydhall type inferrence
      (toMap defs)

let traefikEP2port = \(def : Map/Entry Text EntryPointDef.Type) ->
  let val = def.mapValue
  in
    ComposeServicePort {
    , container_port = Some val.container_port
    , host_port = val.host_port
    }

let TraefikServicePorts = \(defs : TraefikEntryPointDefs.Type) ->
    List/concatMap
      (Map/Entry Text EntryPointDef.Type)
      compose.Port
      traefikEP2port
      (toMap defs)

-- let TraefikUpstreamConfig = \(ep : EntryPointDef)

-- let mkTraefikLabels = \(global : Config.Type) -> \(host : Optional ExternalHost) ->
--   merge {
--   , Some = \(tcfg : TraefikConfig) ->
--     merge {
--     , Some = \(eh : ExternalHost) ->
--       merge {
--       , Auto = [] : Map/Type Text Text
--       , `Text` = \(hostname : Text ) -> [] : Map/Type Text Text
--     , None = [] : Map/Type Text Text
--     } host
--   , None = [] : Map/Type Text Text
--   } global.traefik
      
let mkTraefikService
    =  \(globalCfg : Config.Type)
    -> \(serviceCfg : TraefikConfig.Type)
    -> compose.Service::{
       , image = Some "traefik:${serviceCfg.version}"
       , ports = TraefikServicePorts serviceCfg.entrypoints
       , command = Some (
           compose.StringOrList.List (
             [
             , "--api.insecure=true"
             , "--providers.docker=true"
             , "--providers.docker.exposedbydefault=false"
             , "--log.level=DEBUG"
             , "--accesslog=true"
             ] # (TraefikEntryPointCmdLine serviceCfg.entrypoints)
           )
         )
       , volumes = Some [
         , compose.ServiceVolume.Ref "/var/run/docker.sock:/var/run/docker.sock:ro"
         ]
      }

let mkService
  :  forall(a: Type)
  -> (Config.Type -> a -> compose.Service.Type)
  -> Config.Type
  -> Text
  -> Optional a
  -> Map/Type Text compose.Service.Type
  =  \(a : Type)
  -> \(factory : Config.Type -> a -> compose.Service.Type)
  -> \(globalCfg: Config.Type)
  -> \(serviceName : Text)
  -> \(maybeCfg : Optional a)
  -> merge {
    , Some = \(serviceCfg : a) -> [
        { mapKey = serviceName
        , mapValue = factory globalCfg serviceCfg }
      ]
    , None = Map/empty Text compose.Service.Type
    } maybeCfg

      
let mkCompose = \(cfg : Config.Type)
  -> compose.Compose::{
    , services =
      mkService BackendConfig.Type mkBackendService cfg "backend" cfg.backend
      #
      mkService DBConfig.Type mkDBService cfg "db" cfg.db
      #
      mkService TraefikConfig.Type mkTraefikService cfg "traefik" cfg.traefik
    }

let cfg = Config::{
  , backend = Some BackendConfig::{=}
  , db = Some DBConfig::{=}
  , traefik = Some TraefikConfig::{=}
  }

in
  mkCompose cfg
