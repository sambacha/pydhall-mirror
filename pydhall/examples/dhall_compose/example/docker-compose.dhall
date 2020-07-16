let compose = pydhall+schema:pydhall.examples.dhall_compose.schema::Compose

in
  compose.Compose::{
    , services = toMap {
      , alpine = compose.Service::{
        -- TODO: ommiting `Some`, the error message is messed up
        , image = Some "alpine"
        -- , image = None Text
        }
      }
    }
