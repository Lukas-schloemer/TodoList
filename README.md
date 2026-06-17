# Raspberry Pi Webapp Setup

<!-- markdownlint-disable MD033 -->
<div style="text-align: right; font-size: 0.5em;">Lukas Schlömer in zusammenarbeit mit Tiemen Kroeske</div>
<!-- markdownlint-disable MD033 -->

## 1. Statische IP setzen

Setzt eine feste IP-Adresse für den Raspberry Pi, damit er immer unter derselben Adresse erreichbar ist. Ohne statische IP kann sich die Adresse nach jedem Neustart ändern. Im folgenden werden die Adressen `192.168.24.103/24 und 192.168.24.254, sowie der Port 5000` genutzt. Diese können von Ihren Anforderungen abweichen.

> **Hinweis:** Den Verbindungsnamen (`netplan-eth0`) ggf. mit `nmcli connection show` prüfen und anpassen.

```bash
sudo nmcli connection modify "netplan-eth0" \
  ipv4.addresses 192.168.24.103/24 \
  ipv4.method manual \
  ipv4.gateway 192.168.24.254 \
  ipv4.dns 192.168.24.254
```

Danach Pi neu starten (aus und an).

---

## 2. Users erstellen

Erstellt zwei Benutzer: `willi` als normalen Benutzer und `fernzugriff` als Admin-Benutzer für den SSH-Zugang. Der `fernzugriff`-User wird der Gruppe `sudo` hinzugefügt, damit er administrative Befehle ausführen darf.

> **Hinweis:** Das Passwort wird nach `passwd` interaktiv abgefragt – es erscheint kein Echo beim Tippen.

**Willi:**

```bash
sudo useradd -m willi
sudo passwd willi
```

**Fernzugriff:**

```bash
sudo adduser fernzugriff
sudo usermod -aG sudo fernzugriff
```

---

## 3. SSH aktivieren

Aktiviert den SSH-Dienst, damit der Pi von einem anderen Rechner aus ferngesteuert werden kann. Die Konfiguration schränkt den Zugriff auf den `fernzugriff`-User ein und deaktiviert den direkten Root-Login aus Sicherheitsgründen.

> **Hinweis:** Nach der Konfigurationsänderung muss SSH neugestartet werden, damit die Änderungen wirksam werden.

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

Config editieren:

```bash
sudo nano /etc/ssh/sshd_config
```

Folgendes hinzufügen:

```bash
PermitRootLogin no
PasswordAuthentication yes
AllowUsers fernzugriff
```

SSH neustarten:

```bash
sudo systemctl restart ssh
```

---

## 4. Datum setzen (bei jedem Neustart)

Setzt die Systemzeit manuell, da der Pi ohne Netzwerkzugang oder bei fehlendem RTC-Modul die Zeit nach einem Neustart verliert. Ein falsches Datum kann zu Problemen bei HTTPS-Verbindungen und Logs führen.

> **Hinweis:** Datum und Uhrzeit entsprechend dem aktuellen Zeitpunkt anpassen.

```bash
sudo date -s "2026-05-27 12:10:00"
```

---

## 5. System updaten + Docker installieren

Aktualisiert die Paketlisten und installiert Docker sowie das Compose-Plugin, mit dem später die Container gestartet werden. Mit `hello-world` wird geprüft, ob Docker korrekt funktioniert.

> **Hinweis:** `sudo apt update` lädt nur die Paketlisten herunter – zum eigentlichen Aktualisieren wäre `sudo apt upgrade` nötig.

```bash
sudo apt update
sudo apt install docker.io
sudo systemctl start docker.service
sudo docker run hello-world
sudo apt install docker-compose-plugin
```

---

## 6. Dateien erstellen

Legt alle notwendigen Projektdateien an. Die Inhalte können direkt aus diesem README kopiert werden.

### flaskServer.py

Das Backend der Webapp – eine Flask-REST-API, die Todo-Listen und Einträge im Arbeitsspeicher verwaltet. Läuft auf Port `5000`.

```bash
nano flaskServer.py
```

```python
"""
Requirements:
* flask
"""

import uuid
from flask import Flask, request, jsonify, abort

# initialize Flask server
app = Flask(__name__)

todo_lists = {}
todos = {}

# add some headers to allow cross origin access to the API on this server, necessary for using preview in Swagger Editor!
@app.after_request
def apply_cors_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,DELETE,PATCH'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# define endpoint for getting and deleting existing todo lists
@app.route('/todo-list/<list_id>', methods=['GET', 'DELETE','POST'])
def handle_list(list_id):
    # find todo list depending on given list id
    list_item = None
    for l in todo_lists:
        if l['id'] == list_id:
            list_item = l
            break
    # if the given list id is invalid, return status code 404
    if not list_item:
        abort(404, jsonify('List with the ID {'+list_id+'} does not exist.'))
    if request.method == 'GET':
        # find all todo entries for the todo list with the given id
        print('Returning todo list...')
        return jsonify([i for i in todos if i['list'] == list_id])
    elif request.method == 'DELETE':
        # delete list with given id
        print('Deleting todo list...')
        todo_lists.remove(list_item)
        return jsonify('List deleted.'), 204
    elif request.method == 'POST':
        print('Add todo list...')
        new_item = request.get_json(force=True)
        new_todoId = str(uuid.uuid4())
        newObject = {'id': new_todoId, 'name': new_item['name'] , 'description': new_item['description'] , 'list': list_id}
        todos.append(
            newObject
        )
        print(newObject)
        return newObject, 201

# define endpoint for adding a new list
@app.route('/todo-list', methods=['POST'])
def add_new_list():
    # make JSON from POST data (even if content type is not set correctly)
    new_list = request.get_json(force=True)
    if(new_list['name'] == ''):
        abort(406, jsonify('Request contains faulty Data.'))
    # create id for new list, save it and return the list with id
    new_todoList = {'id': str(uuid.uuid4()), 'name': new_list['name']}
    todo_lists.append(new_todoList)
    return jsonify(new_todoList), 201

@app.route('/entry/<entry_id>', methods=['PATCH', 'DELETE'])
def handle_entry(entry_id):
    # find todo list depending on given list id
    entry_item = None
    for l in todos:
        if l['id'] == entry_id:
            entry_item = l
            break
    # if the given entry id is invalid, return status code 404
    if not entry_item:
        abort(404, jsonify('Entry with the ID {'+entry_id+'} does not exist.'))
    if request.method == 'PATCH':
        # Updates entries for the entry with the given id
        print('Update entry...')
        new_item = request.get_json(force=True)
        newObject =  {'id': entry_id, 'name': new_item['name'], 'description': new_item['description'], 'list': entry_item['list']}
        entry_item.update(newObject)

        return jsonify(newObject), 200
    elif request.method == 'DELETE':
        # delete entry with given id
        print('Deleting entry...')
        todos.remove(entry_item)
        return jsonify('Entry deleted.'), 204

if __name__ == '__main__':
    # start Flask server
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
```

---

### Dockerfile

Definiert das Docker-Image für den API-Server. Installiert Flask und kopiert die Serverdateien ins Image.

```bash
nano Dockerfile
```

```dockerfile
FROM python:3.11-slim
RUN pip install flask
WORKDIR /app
COPY flaskServer.py /app/
COPY templates/ /app/templates/
EXPOSE 5000
CMD ["python", "flaskServer.py"]
```

---

### docker-compose.yaml

Orchestiert den Container.

```bash
nano docker-compose.yaml
```

```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
```

---

## 7. Container starten

Baut das Docker-Image aus den Dockerfile und startet den Container. Beim ersten Start kann es etwas dauern, da das Image erst gebaut werden muss.

> **Hinweis:** Mit `sudo docker compose up --build` wird das Image bei Änderungen neu gebaut. Mit `Strg+C` werden die Container gestoppt.

```bash
sudo docker compose up
```

Danach erreichbar:

**API:** <http://192.168.24.103:5000>

---
