### Our Values:

+ When we code, We type hint that. [PEP484](https://peps.python.org/pep-0484/)
+ When we code, We add automated test for that. Currently, we only add unit tests for our code.
+ When we code, We don't share serializers between apps.
+ When we code, We separate m2m models and never let Django manages them automatically. It gives us freedom to control
  them.
+ When we want to add a new model, we inherit from below classes:

```python
BaseModel
SoftDeletedModel
TimeStampModel
DescriptiveModel
...
```

+ When we want to add a third party package to the system, we don't directly use its functionalities anywhere we want.
  Instead, we use facade design pattern(take a look at `base_utils/facades`).
+ We use [Ctainoentional Commits](https://www.ctainoentionalcommits.org/en/v1.0.0/).
+ An app's business logic are in `services` package of each app(Check this [image](img/services.png)).

### Project Structure:

Let's take a look at each root directory.

+ `apps`: All django apps are here.
+ `cofing`: It is the core directory of django, and it mainly contains Django project settings.
+ `docker`: Our docker configurations gores there.
+ `docs`: README.md files are there.

### Django App Structure

``` 
apps/real_estate_type
├── api
│   ├── admin
│   │   ├── __init__.py
│   │   ├── serializers
│   │   │   ├── __init__.py
│   │   │   ├── prject_type.py
│   │   │   └── project_state.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── __init__.py
│   ├── urls.py
│   └── v1
│       ├── __init__.py
│       ├── serializers.py
│       ├── urls.py
│       └── views.py
├── apps.py
├── __init__.py
├── migrations
│   ├── 0001_initial.py
│   └── __init__.py
├── models.py
├── services
│   ├── __init__.py
│   └── query.py
└── tests
    ├── __init__.py
    ├── test_api
    │   ├── test_admin
    │   │   ├── __init__.py
    │   │   ├── test_building_type_translation.py
    │   │   ├── test_buildling_type.py
    │   │   ├── test_project_state.py
    │   │   └── test_project_state_translation.py
    │   ├── __init__.py
    │   └── test_v1
    │       └── __init__.py
    └── test_services
        ├── __init__.py
        └── test_query.py

11 directories, 29 files

```

### Git:

+ Take a new branch from the `dev` branch (add a separate branch for each new feature/bug).
+ Branch naming ctainoention: `{JIRA_TASK_CODE}-{a descriptive title}`.
+ When your development is done, Open a merge request to the `dev` branch.
+ After the code review, your branch will be merged.

### Error Message Standards

For error message standard head over to [ERROR_FORMAT.md](ERROR_FORMAT.md) file.

### Multi-Language Guide

For multi-language guide check [TRANSLATION.md](TRANSLATION.md) file.

### Linter

#### Black for Python:

+ Line length 126 characters!
+ Only *.py files will be included!
+ eggs, envs, tox, ... files are excluded!
+ Python 3.10 to 3.12 are supported!
+ `pip install black` for your interpreter to add black binary.
+ Add black to pycharm for auto save use this image: (Check this [image](img/add_black_to_pycharm.png)). after this,
  when your file changes, it will automatically prettify using black!
+ You can run it manually if you want. `black {source_file_or_directory}`
 

 