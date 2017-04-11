// Copyright © 2017, ACM@UIUC
//
// This file is part of the Groot Project.  
// 
// The Groot Project is open source software, released under the 
// University of Illinois/NCSA Open Source License. You should have
// received a copy of this license in a file with the distribution.


extern crate iron;

use iron::prelude::*;
use iron::{Handler};
use iron::status;

mod router;

fn canopy_server() {
    let mut router = router::Router::new();

    router.add_route("hello".to_string(), |_: &mut Request| {
        Ok(Response::with((status::Ok, "Hello world !")))
    });

    router.add_route("hello/again".to_string(), |_: &mut Request| {
       Ok(Response::with((status::Ok, "Hello again !")))
    });

    router.add_route("error".to_string(), |_: &mut Request| {
       Ok(Response::with(status::BadRequest))
    });

    Iron::new(router).http("localhost:3000").unwrap();
}