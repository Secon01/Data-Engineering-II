# Assignment 3 — Task 1 Code Reference

## Repository
`https://github.com/sztoor/model_serving.git`

---

## app.py
`model_serving/single_server_without_docker/production_server/app.py`

```python
from workerA import add_nums, get_accuracy, get_predictions

from flask import (
    Flask,
    request,
    jsonify,
    Markup,
    render_template
)

#app = Flask(__name__, template_folder='./templates',static_folder='./static')
app = Flask(__name__)

@app.route("/")
def index():
    return '<h1>Welcome to the Machine Learning Course.</h1>'

@app.route("/accuracy", methods=['POST', 'GET'])
def accuracy():
    if request.method == 'POST':
        r = get_accuracy.delay()
        a = r.get()
        return '<h1>The accuracy is {}</h1>'.format(a)

    return '''<form method="POST">
    <input type="submit">
    </form>'''

@app.route("/predictions", methods=['POST', 'GET'])
def predictions():
    if request.method == 'POST':
        results = get_predictions.delay()
        predictions = results.get()

        results = get_accuracy.delay()
        accuracy = results.get()

        final_results = predictions

        return render_template('result.html', accuracy=accuracy, final_results=final_results)

    return '''<form method="POST">
    <input type="submit">
    </form>'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=True)
```

---

## workerA.py
`model_serving/single_server_without_docker/production_server/workerA.py`

```python
from celery import Celery

from numpy import loadtxt
import numpy as np
from tensorflow.keras.models import model_from_json

model_json_file = './model.json'
model_weights_file = './model.h5'
data_file = './pima-indians-diabetes.csv'

def load_data():
    dataset = loadtxt(data_file, delimiter=',')
    X = dataset[:,0:8]
    y = dataset[:,8]
    y = list(map(int, y))
    y = np.asarray(y, dtype=np.uint8)
    return X, y

def load_model():
    # load json and create model
    json_file = open(model_json_file, 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    # load weights into new model
    loaded_model.load_weights(model_weights_file)
    #print("Loaded model from disk")
    return loaded_model

# Celery configuration
CELERY_BROKER_URL = 'pyamqp://guest@localhost//'
CELERY_RESULT_BACKEND = 'rpc://'
# Initialize Celery
celery = Celery('workerA', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@celery.task()
def add_nums(a, b):
    return a + b

@celery.task
def get_predictions():
    results = {}
    X, y = load_data()
    loaded_model = load_model()
    # predictions = loaded_model.predict_classes(X)
    predictions = np.round(loaded_model.predict(X)).flatten().astype(np.int32)
    results['y'] = y.tolist()
    results['predicted'] = predictions.tolist()
    return results

@celery.task
def get_accuracy():
    X, y = load_data()
    loaded_model = load_model()
    loaded_model.compile(loss='binary_crossentropy', optimizer='rmsprop', metrics=['accuracy'])
    score = loaded_model.evaluate(X, y, verbose=0)
    #print("%s: %.2f%%" % (loaded_model.metrics_names[1], score[1]*100))
    return score[1]*100
```

---

## run_task.py
`model_serving/single_server_without_docker/production_server/run_task.py`

```python
from workerA import add_nums
import time

if __name__ == '__main__':
    for _ in range(1):
        result = add_nums.delay(10, 22)
        time.sleep(2)
        print('Task finished?', result.ready())
        print('Task result:', result.result)
        print('get result"', result.get(timeout=1))
```

---

## cloud-cfg.txt
`model_serving/openstack-client/single_node_without_docker_client/cloud-cfg.txt`

```yaml
#cloud-config

apt_update: true
apt_upgrade: true
packages:
  - python3-pip
  - python3-dev
  - build-essential
  - rabbitmq-server

byobu_default: system

runcmd:
  - pip3 install "celery" "tensorflow==2.10.0" "amqp" "flask==2.3.1" "future" "numpy<2.0"
  - git clone https://github.com/sztoor/model_serving.git
  - celery --workdir=/model_serving/single_server_without_docker/production_server -A workerA worker --detach --loglevel=debug --concurrency=1 -n wkr1@backend
  - python3 /model_serving/single_server_without_docker/production_server/app.py --host=0.0.0.0 --port=5100 &
```

---

## start_instance.py
`model_serving/openstack-client/single_node_without_docker_client/start_instance.py`

```python
# http://docs.openstack.org/developer/python-novaclient/ref/v2/servers.html
import time, os, sys, random
import inspect
from os import environ as env

from novaclient import client
import keystoneclient.v3.client as ksclient
from keystoneauth1 import loading
from keystoneauth1 import session

flavor = "ssc"                          # ← MUST EDIT: exact flavor name from openstack flavor list
private_net = "Cloud_Network"           # ← MUST EDIT: exact network name from openstack network list
floating_ip_pool_name = None
floating_ip = None
image_name = "<use_Ubuntu_20.04_image>" # ← MUST EDIT: exact image name from openstack image list

identifier = random.randint(1000, 9999)

loader = loading.get_plugin_loader('password')

auth = loader.load_from_options(
    auth_url=env['OS_AUTH_URL'],
    username=env['OS_USERNAME'],
    password=env['OS_PASSWORD'],
    project_name=env['OS_PROJECT_NAME'],
    project_domain_id=env['OS_PROJECT_DOMAIN_ID'],
    #project_id=env['OS_PROJECT_ID'],
    user_domain_name=env['OS_USER_DOMAIN_NAME']
)

sess = session.Session(auth=auth)
nova = client.Client('2.1', session=sess)
print("user authorization completed.")

image = nova.glance.find_image(image_name)
flavor = nova.flavors.find(name=flavor)

if private_net != None:
    net = nova.neutron.find_network(private_net)
    nics = [{'net-id': net.id}]
else:
    sys.exit("private-net not defined.")

cfg_file_path = os.getcwd() + '/cloud-cfg.txt'
if os.path.isfile(cfg_file_path):
    userdata = open(cfg_file_path)
else:
    sys.exit("cloud-cfg.txt is not in current working directory")

secgroups = ['default']

print("Creating instance ... ")
instance = nova.servers.create(
    name="prod_server_without_docker_" + str(identifier),
    image=image,
    key_name='sztoor',       # ← MUST EDIT: your keypair name (e.g. 'de2-course-key')
    flavor=flavor,
    userdata=userdata,
    nics=nics,
    security_groups=secgroups
)

inst_status = instance.status
print("waiting for 10 seconds.. ")
time.sleep(10)

while inst_status == 'BUILD':
    print("Instance: " + instance.name + " is in " + inst_status + " state, sleeping for 5 seconds more...")
    time.sleep(5)
    instance = nova.servers.get(instance.id)
    inst_status = instance.status

print("Instance: " + instance.name + " is in " + inst_status + " state")
```

---

## What needs to be edited in start_instance.py before running

| Variable | Current value | What to set |
|----------|--------------|-------------|
| `flavor` | `"ssc"` | Run `openstack flavor list` and use the exact name |
| `private_net` | `"Cloud_Network"` | Run `openstack network list` and use the exact name |
| `image_name` | `"<use_Ubuntu_20.04_image>"` | Run `openstack image list` and use the exact Ubuntu 22.04 name |
| `key_name` | `'sztoor'` | Change to your keypair name e.g. `'de2-course-key'` |

---

## Client VM Info (Task 1)
- **VM name**: client-vm-sotiris
- **Floating IP**: 130.238.27.142
- **Private IP**: 192.168.2.158
- **Keypair**: de2-course-key2
- **SSH**: `ssh -i ~/.ssh/de2-course-key ubuntu@130.238.27.142`
