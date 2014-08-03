#!/usr/bin/python
#coding=utf-8
#app path build-ups
# author Rowland
# edit 2014-03-19 14:17:30

import os
import sys
import json
import getopt
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'lib'))

import tornado.ioloop
import tornado.web
from tornado.log import access_log, gen_log

import path
from util.route import Router
from util.tools import Log
from configer import JsonConfiger


class Xroute(tornado.web.RequestHandler):
    '''doorlet'''
    def prepare(self):
        # 分析请求参数
        self.json_args = {}
        # json格式请求
        if self.request.headers.get('Content-Type', '').find("application/json") >= 0:
            try:
                self.json_args = json.loads(self.request.body)
                return
            except Exception as ex:
                self.send_error(400)
                return
        # 普通参数请求
        else:
            self.json_args = dict((k, v[-1]) for k, v in self.request.arguments.items())
        
    @tornado.web.asynchronous
    def get(self, path):
        Router.get(path, self)
        
    @tornado.web.asynchronous
    def post(self, path):
        Router.post(path, self)
        
    @tornado.web.asynchronous
    def put(self, path):
        Router.put(path, self)
        
    @tornado.web.asynchronous
    def delete(self, path):
        Router.delete(path, self)


def get_application():
    return tornado.web.Application([(r"^/([^\.|]*)(?!\.\w+)$", Xroute)],
                log_function=log_request)


def init_application(conf_file):
    os.chdir(os.path.join(os.path.dirname(__file__), '..'))
    confs = JsonConfiger()
    confs.load_file(conf_file)
    log_cnf = confs.get('logging')
    if log_cnf['config_file'][:1] not in ['/', '\\']:
        log_cnf['config_file'] = os.path.join(
            os.path.dirname(os.path.abspath(conf_file)),
            log_cnf['config_file'])
    Log.set_up(log_cnf)
    return confs


def log_request(handler):
    """http日志函数
    """
    if handler.get_status() < 400:
        log_method = access_log.info
    elif handler.get_status() < 500:
        log_method = access_log.warning
    else:
        log_method = access_log.error
    req = handler.request
    log_method('"%s %s" %d %s %.6f',
               req.method, req.uri, handler.get_status(),
               req.remote_ip, req.request_time() )


if __name__=="__main__":
    # init
    port = 8888
    includes = None
    opts, argvs = getopt.getopt(sys.argv[1:], "c:p:h")
    for op, value in opts:
        if op == '-c':
            includes = value
        elif op == '-p':
            port = int(value)
        elif op == '-h':
            print u'''使用参数启动:
                        usage: [-p|-c]
                        -p [prot] ******启动端口,默认端口:%d
                        -c <file> ******加载配置文件
                   ''' % port
            sys.exit(0)
    if not includes:
        includes = os.path.join(path._ETC_PATH, 'includes_dev.json')
        print "no configuration found!,will use [%s] instead" % includes
    # main
    confs = init_application(includes)
    logger = Log().getLog()
    logger.info("starting..., listen [%d], configurated by (%s)", port, includes)
    application = get_application()
    application.listen(port)
    tornado.ioloop.IOLoop.instance().start()

