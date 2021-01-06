![banner.js](/static/banner.jpg)

**elekto** is an opensource organization wide application for conducting community elections. It provides the necessary support for conducting elections with security. 

elekto is built upon the **CIVS's** voting logic know as **Condorcet method** (and has an ability to extend to other logics as well).

### To start using elekto

See our detailed instruction [docs](/docs/README.md)

### To start developing elekto

See the application's design and architecture [documentation](/docs/DESIGN.md), that has all information about building elekto from source, how to contribute code and documentation, who to contact about what, etc.

The repository contains an conda `environment.yml` file for creating virtual environment (refer to - [conda docs](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)) and also has an `requirements.txt` for pip usage.

```bash
# Installation with pip 
pip install -r requirements.txt

# Installation with Conda
conda env create -f environment.yml
conda activate k8s
```

To run the flask local server, use the `console` script in the repository. The flask server will start on `5000` by default but can be changed using `--port` option
```bash
# to run the server on default configs
python console

# to change host and port
python console --port 8080 --host 0.0.0.0

# to migrate the database from command line 
python console --migrate
```

### Support 

if you have questions, reach out to us one way or another.
