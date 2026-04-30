# Writing a New Article

This guide explains how to add new content to the ucl-open documentation site, which is built with [DocFX](https://dotnet.github.io/docfx/).

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| [Git](https://git-scm.com/) | Version control | Required |
| [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0) | Building the site with DocFX | Required |
| [Bonsai](https://bonsai-rx.org/) | Generating workflow SVGs | Required for workflow diagrams |

## Site structure

```
docs/                   ← root
├── docfx.json          ← build configuration
├── toc.yml             ← top-level navigation (tabs)
├── index.md            ← landing page
├── docs/               ← general documentation section
│   ├── toc.yml
│   └── *.md
└── tutorials/          ← step-by-step tutorials section
    ├── toc.yml
    └── *.md
```

The top-level `toc.yml` defines the navigation tabs. Each tab points to a subfolder that has its own `toc.yml` controlling the sidebar links within that section.

## Adding a new page

### 1. Create the markdown file

Add a `.md` file to the appropriate section folder:

- **`docs/`**: reference material, conceptual overviews.
- **`tutorials/`**: how-to guides, step-by-step walkthroughs with a defined start and end

Use lowercase kebab-case for filenames, e.g. `hardware-modules.md`.

### 2. Register it in the section TOC

Open the `toc.yml` in the same folder and add an entry:

```yaml
- name: My New Article
  href: my-new-article.md
```

Entries appear in the sidebar in the order they are listed. To create a nested group:

```yaml
- name: Hardware
  items:
  - name: Adding a hardware module
    href: hardware-modules.md
  - name: Adding a logging module
    href: logging-modules.md
```

### 3. Add a new top-level section

To add a new tab to the top navigation, create a new subfolder with its own `toc.yml`, then register it in the root `toc.yml`:

```yaml
- name: My Section
  href: my-section/
```

## Markdown features

DocFX supports standard GitHub-flavoured Markdown plus several extensions.

### Cross-references and links

Link to other pages using relative paths:

For example:

```markdown
See the [Project Structure](project-structure.md) page.
See the [ucl-open](https://github.com/ucl-open) website.
```

### Alerts

```markdown
> [!NOTE]
> Informational note.

> [!TIP]
> Helpful tip.

> [!WARNING]
> Something the reader should be careful about.

> [!IMPORTANT]
> Critical information.
```

### Code blocks

Fence code with triple backticks and a language identifier for syntax highlighting:

For example: 

```` markdown
```python
from ucl_open.rigs.base import BaseSchema
```
````

### Images

Place image files in the `images/` folder at the root of the docs directory (it is registered as a resource in `docfx.json`). Reference them with a relative path:

```markdown
![Alt text](../images/my-diagram.png)
```

### Bonsai workflow diagrams

Workflows are embedded using the `:::workflow` custom container:

```markdown
:::workflow
![My Workflow](~/assets/workflows/MyWorkflow.bonsai)
:::
```

This renders an SVG diagram of the workflow with a button to copy the XML. The `.bonsai` file must be placed in `assets/workflows/`, and a matching `.svg` must be generated alongside it.

**Generating SVGs**

Place your `.bonsai` file in `assets/workflows/` and run the export script from the `docs/` root:

```powershell
.\bonsai\modules\Export-Image.ps1 -workflowPath .\assets\workflows -bootstrapperPath ..\acquisition\.bonsai\Bonsai.exe
```

This calls `Bonsai.exe --export-image` on each workflow and post-processes the SVG for dark mode. If your Bonsai environment is elsewhere, adjust the `-bootstrapperPath` accordingly.

Commit both the `.bonsai` and the `.svg` files.

## Contributing via pull request

The `main` branch is protected — changes must be submitted via a pull request (PR).

### 1. Create a branch

Open the Source Control panel (`Ctrl+Shift+G`). Click the **...** menu at the top of the panel and select **Branch > Create Branch...**. Enter a short descriptive name, e.g. `add-logging-tutorial` or `fix-hardware-module-typos`, and press `Enter`.

### 2. Make your changes

Add or edit files as described above. As you save files, they appear under **Changes** in the Source Control panel. Hover a file and click **+** to stage it, or click **+ Stage All Changes** to stage everything at once.

Enter a brief commit message in the text box at the top of the panel and click **Commit**.

### 3. Push the branch and open a pull request

After committing, click **Publish Branch** (if the branch has not been pushed yet) or **Sync Changes** in the Source Control panel. VSCode will push the branch to GitHub.

To open a pull request, click the GitHub icon in the Activity Bar and select **Create Pull Request**, or follow the link that appears in the notification popup after pushing. Fill in a title and description, then click **Create**.

Set a maintainer as a reviewer. Once approved, the PR is merged into `main` and the site is rebuilt and deployed.

> [!TIP]
> You can preview the site locally before pushing.

## Building and previewing locally

Ensure you have the `docfx` tool installed:

```
dotnet tool install -g docfx
```

From the root `docs/` directory, run:

```
docfx --serve
```

This builds the site to `_site/` and starts a local server at `http://localhost:8080`. The site will rebuild automatically when you save changes.

To build without serving:

```
docfx build
```

> [!NOTE]
> The `_site/` output folder is git-ignored. Never commit it.
