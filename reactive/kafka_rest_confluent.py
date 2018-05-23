import os
import socket
import charms.apt
from jujubigdata import utils
from charms.reactive import (
    set_flag,
    clear_flag,
    when,
    when_not,
    endpoint_from_flag,
    data_changed,
)
from charmhelpers.core.hookenv import (
    status_set,
    open_port,
    config,
    log,
    charm_dir,
)
from charmhelpers.core.templating import render
from charmhelpers.core.host import (
    service_running,
    service_start,
    service_stop,
)


@when_not('kafka-rest-confluent.installed')
def install_kafka_rest_confluent():
    charms.apt.queue_install(['confluent-kafka-rest', 'openjdk-8-jre'])
    set_flag('kafka-rest-confluent.installed')


@when('apt.installed.confluent-kafka-rest',
      'apt.installed.openjdk-8-jre')
@when_not('kafka.ready')
def waiting_kafka():
    status_set('blocked', 'Waiting on Kafka relation')


@when_not('config.set.port')
def waiting_port_config():
    status_set('blocked', 'Waiting on port config')


@when('apt.installed.confluent-kafka-rest',
      'apt.installed.openjdk-8-jre')
@when_not('kafka-rest-confluent.systemd')
def configure_kafka_rest_systemd():
    # Create user and configuration dir
    dc = utils.DistConfig(filename='{}/files/setup.yaml'.format(charm_dir()))
    dc.add_users()
    dc.add_dirs()
    # Create systemd service file
    render(source='confluent-kafka-rest.service.j2',
           target='/etc/systemd/system/confluent-kafka-rest.service',
           context={})
    set_flag('kafka-rest-confluent.systemd')


@when('apt.installed.confluent-kafka-rest',
      'apt.installed.openjdk-8-jre',
      'config.set.port',
      'kafka.ready')
@when_not('kafka-rest-confluent.setup')
def setup_kafka_rest():
    if service_running('confluent-kafka-rest'):
        service_stop('confluent-kafka-rest')
    kafka = endpoint_from_flag('kafka.ready')
    kafka_brokers = []
    for broker in kafka.kafkas():
        kafka_brokers.append("{}:{}".format(broker['host'], broker['port']))
    zookeepers = []
    for zoo in kafka.zookeepers():
        zookeepers.append("{}:{}".format(zoo['host'], zoo['port']))
    # Remove duplicate Zookeeper entries since every Kafka broker unit
    # sends all Zookeeper info.
    zookeepers = list(set(zookeepers))
    port = config().get('port')

    render(source="kafka-rest.properties.j2",
           target='/etc/kafka-rest/kafka-rest.properties',
           context={
               'id': os.environ['JUJU_UNIT_NAME'].replace('/', '-'),
               'zookeepers': zookeepers,
               'brokers': kafka_brokers,
               'hostname': socket.gethostname(),
               'listener': str(port),
            })
    
    service_start('confluent-kafka-rest')
    open_port(port)
    status_set('active', 'ready')
    set_flag('kafka-rest-confluent.setup')


@when('endpoint.available',
      'config.set.port',
      'kafka-rest-confluent.setup')
def http_endpoint():
    endpoint = endpoint_from_flag('endpoint.available')
    endpoint.configure(port=config().get('port'))


@when('config.changed.port',
      'kafka-rest-confluent.setup')
def config_changed_port():
    clear_flag('kafka-rest-confluent.setup')


@when('kafka-rest-confluent.setup',
      'kafka.ready')
def check_kafka_changed():
    kafka = endpoint_from_flag('kafka.ready')
    if data_changed('kafka-info', kafka.kafkas()):
        clear_flag('kafka-rest-confluent.setup')
