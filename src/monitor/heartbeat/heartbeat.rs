// Copyright © 2017, ACM@UIUC
//
// This file is part of the Groot Project.  
// 
// The Groot Project is open source software, released under the 
// University of Illinois/NCSA Open Source License. You should have
// received a copy of this license in a file with the distribution.


extern crate hyper;

use hyper::*;
use std::io::Read;

struct Heart {
    String Applications;
}

impl Heartbeat {
   pub fn Beat() {
       let client = Client::new();
       let res = client.post("http://localhost:3000/set").body(r#"{ "msg": "Just trust the Rust" }"#).send().unwrap();
       assert_eq!(res.status, hyper::Ok);
       let mut res = client.get("http://localhost:3000/").send().unwrap();
       assert_eq!(res.status, hyper::Ok);
       let mut s = String::new();
       res.read_to_string(&mut s).unwrap();
       println!("{}", s); 
   }

   pub fn new(String: Apps) -> self {
       Heart {Applications: Apps}
   }
}
