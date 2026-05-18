# Building and Deploying

### Template Project
In order for ucl-open projects to have a somewhat standardised structure, a [copier](https://copier.readthedocs.io/en/stable/) template is [provided](https://github.com/ucl-open/rig-template) as part of the framework. 

First, install the `copier` tool from the command line (should only need to be done once per machine):

```
uv tool install copier
```

Next, run `copier` with the ucl-open [rig template](https://github.com/ucl-open/rig-template) in the directory where you want to create your new project:

```
copier copy --vcs-ref main https://github.com/ucl-open/rig-template.git ./my-new-project
```
`copier` will prompt you for some basic template variables and then generate required files and directory structure.

### Initialize Git Tracking
It is good practice to track changes to the project with [Git](https://git-scm.com/), and to maintain a remote repository of those changes with [GitHub](https://github.com/).

Navigate into your newly created project folder and initialize a local git repository:
```
cd my-new-project
git init -b main
```

Make an initial commit:
```
git add .
git commit -m "Deploy new ucl-open rig"
```

Using a browser create a new, empty repository on GitHub (e.g. under your personal account, or your institution's organisation account) with the same name as your local project. Set this GitHub repository as the `remote` for your project:
```
git remote add origin https://github.com/<github-account>/my-new-project.git
```

Push your local changes to the `remote` repository:
```
git push -u origin main
```

### Deploy Project
The ucl-open template comes with a script to 'bootstrap' the Python and Bonsai development environments, run this with:
```
.\scripts\deploy.ps1
```