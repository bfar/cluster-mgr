import rrdtool
import os
import time
import psutil
import re

from ldap3 import Server, Connection, BASE

searchlist = {
'total_connections':('cn=Total,cn=Connections,cn=Monitor','monitorCounter', '#'),
'bytes_sent': ('cn=Bytes,cn=Statistics,cn=Monitor','monitorCounter','Bytes'),
'completed_operations': ('cn=Operations,cn=Monitor','monitorOpCompleted', '#'),
'initiated_operations': ('cn=Operations,cn=Monitor','monitorOpInitiated', '#'),
'referrals_sent': ('cn=Referrals,cn=Statistics,cn=Monitor','monitorCounter', '#'),
'entries_sent': ('cn=Entries,cn=Statistics,cn=Monitor','monitorCounter', '#'),
'bind_operations': ('cn=Bind,cn=Operations,cn=Monitor','monitorOpCompleted', '#'),
'unbind_operations': ('cn=Unbind,cn=Operations,cn=Monitor','monitorOpCompleted', '#'),
'add_operations': ('cn=Add,cn=Operations,cn=Monitor','monitorOpInitiated', '#'),
'delete_operations':  ('cn=Delete,cn=Operations,cn=Monitor','monitorOpCompleted', '#'),
'modify_operations': ('cn=Modify,cn=Operations,cn=Monitor','monitorOpCompleted', '#'),
'compare_operations': ('cn=Compare,cn=Operations,cn=Monitor','monitorOpCompleted', '#'),
'search_operations': ('cn=Search,cn=Operations,cn=Monitor','monitorOpCompleted', '#'),
'write_waiters': ('cn=Write,cn=Waiters,cn=Monitor','monitorCounter', '#'),
'read_waiters': ('cn=Read,cn=Waiters,cn=Monitor','monitorCounter', '#'),
}



data_path = '/var/monitoring'


def query_ldap_and_inject_db(addr, binddn, passwd):
    
    server = Server(addr, use_ssl=True)
    conn = Connection(server, user=binddn, password=passwd)
    conn.bind()

    summary = {}

    for key in searchlist.keys():
        b = searchlist[key][0]
        attr = searchlist[key][1]

        conn.search(search_base=b, search_scope=BASE,
                    search_filter='(objectClass=*)',
                    attributes=['+'])

        summary[key]=conn.response[0]['attributes'][attr][0]

    options = summary.keys()
    options.sort()
    data = [ summary[o] for o in options]
    data.insert(0,'N')
    datas = ':'.join(data)
    
    rrdtool.update(os.path.join(data_path, 'ldap.rrd'), str(datas))


    z=time.gmtime(time.time()-300)


    ct = time.strftime("%Y%m%d%H%M%S.000Z",z)
    
    conn.search(search_base="o=gluu", search_filter='(&(&(objectClass=oxMetric)(creationDate>={}))(oxMetricType=user_authentication_failure))'.format(ct), attributes=["oxData"])

    data_s=conn.response[-1]["attributes"]['oxData'][0]
    m=re.search('{"count":(?P<count>\d+)}', data_s)
    failure=m.group('count')

    conn.search(search_base="o=gluu", search_filter='(&(&(objectClass=oxMetric)(creationDate>={}))(oxMetricType=user_authentication_success))'.format(ct), attributes=["oxData"])
    data_s=conn.response[-1]["attributes"]['oxData'][0]
    m=re.search('{"count":(?P<count>\d+)}', data_s)
    success=m.group('count')

    
    datas = 'N:{}:{}'.format(success, failure)
    print datas
    rrdtool.update(os.path.join(data_path, 'gluu_auth.rrd'), datas)

    conn.unbind()

def inject_cpu_info():
    sl=open("/proc/stat").readline()
    user, nice, system, idle, iowait, irq, softirq, steal, guest, guestnice = sl.strip().split()[1:]
    file_path = os.path.join(data_path, 'cpu_info.rrd')
    datas = 'N:{0}:{1}:{2}:{3}:{4}:{5}:{6}:{7}:{8}:{9}'.format(
                                        user,
                                        nice,
                                        system,
                                        idle,
                                        iowait,
                                        irq,
                                        softirq,
                                        steal,
                                        guest, 
                                        guestnice,
                                    )


    rrdtool.update(file_path, datas)
    
def inject_load_average():  
    file_path = os.path.join(data_path, 'load_average.rrd')
    load_avg = os.getloadavg()
    data = "N:{}".format(load_avg[0])
    rrdtool.update(file_path, data)


def get_rrd_indexes(rrd_file):
    ds_list = []
    inf = rrdtool.info(rrd_file)
    for k in inf:
        rs = re.search('ds\[(?P<ds>[\w?]+)\].index', k)
        if rs:
            ds = rs.group('ds')
            ds_list.append((int(inf[k]), ds))
    
    ds_list.sort()

    return ds_list


def inject_disk_usage():
    rrd_file = os.path.join(data_path, 'disk_usage.rrd')
    rrd_i = get_rrd_indexes(rrd_file)
    disk_usage_data = ['N']
    disks = psutil.disk_partitions()

    for ri in rrd_i:
        for d in disks:
            if d.device == ri[1].replace('_','/'):
                mp = d.mountpoint
                du = psutil.disk_usage(mp)
                disk_usage_data.append(str(du.percent))
                break
        else:
            disk_usage_data.append('0')

    datas = ':'.join(disk_usage_data)
    rrdtool.update(rrd_file, datas)


def inject_mem_usage():  
    file_path = os.path.join(data_path, 'mem_usage.rrd')
    mem_usage = psutil.virtual_memory()
    data = "N:{}".format(mem_usage.percent)
    rrdtool.update(file_path, data)


def inject_ne_io():
    rrd_file = os.path.join(data_path, 'net_io.rrd')
    rrd_i = get_rrd_indexes(rrd_file)
    disk_usage_data = ['N']
    net = psutil.net_io_counters(pernic=True)
    
    for ri in rrd_i:
        fa = ri[1].find('_')
        nif = ri[1][:fa]
        t = ri[1][fa+1:]
        val = getattr(net[nif], t)
        disk_usage_data.append( str(val) )

    datas = ':'.join(disk_usage_data)
    rrdtool.update(rrd_file, datas)


query_ldap_and_inject_db('ldaps://c4.gluu.org:1636', "cn=directory manager,o=gluu", "secret")
"""
inject_cpu_info()
inject_load_average()
inject_disk_usage()
inject_mem_usage()
inject_ne_io()
"""