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

use std::collections::HashMap;

pub struct Router {
    // Routes here are simply matched with the url path.
    routes: HashMap<String, Box<Handler>>
}

impl Router {
    pub fn new() -> Self {
        Router { routes: HashMap::new() }
    }

    pub fn add_route<H>(&mut self, path: String, handler: H) where H: Handler {
        self.routes.insert(path, Box::new(handler));
    }
}

impl Handler for Router {
    fn handle(&self, req: &mut Request) -> IronResult<Response> {
        match self.routes.get(&req.url.path().join("/")) {
            Some(handler) => handler.handle(req),
            None => Ok(Response::with(status::NotFound))
        }
    }
}