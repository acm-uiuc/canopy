# canopy
Service health monitor for groot

[![Build Status](https://travis-ci.org/acm-uiuc/canopy.svg?branch=master)](https://travis-ci.org/acm-uiuc/canopy)


[![Join the chat at https://acm-uiuc.slack.com/messages/C6XGZD212/](https://img.shields.io/badge/slack-groot-724D71.svg)](https://acm-uiuc.slack.com/messages/C6XGZD212/)

# Instructions - Python 2.7
 - Install dependencies with `pip install -r requirements.txt`
 - Run server with `python src/server/canopy-server.py start`
 - Run client with `python src/server/canopy-client.py start`
 - Client and server logs are saved in `/tmp/canopyclient.log` and `/tmp/canopyserver.log`, respectively.
 - Stop server with `python src/server/canopy-server.py stop`
 - Stop server with `python src/server/canopy-client.py stop`

# Configuration Options

### Server
 - `host` and `port` can be set to any valid address and port
 - `timeout` should be set higher than the highest client `hb_interval`
 - `silent` should be `false` unless there is a good reason not to log

### Client
 - `parent_host` and `parent_port` should point to the node's immediate parent
 - `host` and `port` are used for listening, and is used if this node is not a leaf
 - `app_name` is the human-readable name for process monitored by node
 - `hb_interval` (seconds) must be less than parent node's timeout
 - `timeout` should be set higher than highest client `hb_interval`
 - `silent` should be `false` unless there is a good reason not to log
 - `is_leaf` is `true` only on a leaf node
 - `target` is the *command* that should be run and logged by this node

# Design
Canopy is designed to act as a distributed monitoring service for the Groot system in ACM@UIUC.
It provides status monitoring, logging, and management as a RESTful API, and integrates with the existing Docker infrastructure.

Canopy is structured as a tree, where the structure beyond the two adjacent layers is abstracted. 
The root of this tree connects to the Groot API Gateway and runs a Canopy Server instance.
Other physical or virtual machines running microservices can connect to this network using Canopy Clients, which come in two flavors:
 - Relays do not specifically monitor a process, but act as intermediaries between the root and leaves
 - Leaves run microservice processes, and are responsible for collecting logs and executing commands

Heartbeats filter from leaves through relays towards the root, and can be used to monitor the health of the Groot ecosystem, and provide early detection for errors.

Logs are stored at leaves, and snapshots or streams of these logs can be sent to the root upon request.

Command logic can be run at any level in the tree, and are executed by the leaves. This includes starting or terminating processes, delivering signals, or performing load balancing. 
