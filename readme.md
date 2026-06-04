# The Relational Database Normaliser

This tool takes as input a database schema with SQL nullable attributes, and with key, functional, multivalued, inclusion, disjoint, and covering dependencies, and outputs, whenever formally possible, its sixth normal form.

#### Declarations:

- database schema declaration: `database schema DBNAME`
- relation declaration: `relation RNAME: A B`
- SQL nullable attributes declaration: nullable: A B

If no database schema is declared, the input is treated as the default database
schema. 
Database schemas, relations, and attributes are named globally. 
Attributes may be nullable.

#### Dependency syntax:

- functional dependencies: `A B -> C D`
- key-style functional dependencies: `A B -> att(RNAME)`
- multivalued dependencies: `A B ->> C`
- implies SQL-null dependencies: `A -N-> B`
- jointly SQL-null dependencies: `A <-N-> B`
- alternative SQL-null dependencies: `A ->N<- B`
- inclusion dependencies: `A B => C D`
- equality inclusion dependencies: `A B == C D`
- covering inclusion dependencies: `A B o=> C D`
- disjoint inclusion dependencies: `A B x=> C D`

Join dependencies (FDs and MVDs) and SQL-null dependencies must be contained in
one relation. For inclusion dependencies, the left side must be contained in one
relation, the right side must be contained in one relation, and both sides must
have the same arity.

#### Example:

```
   database schema Registry:
   relation T: ssn empid name hdate phone email dept manager
   nullable: empid hdate dept manager
   empid -N-> dept
   dept <-N-> manager
   empid <-N-> hdate
   ssn -> name
   ssn ->> phone
   ssn ->> email
   ssn -> empid
   empid -> ssn
   empid -> hdate
   empid -> dept
   dept -> manager
   manager => empid
```

### Desktop launcher:

The desktop launcher starts the local Normaliser server on an available port and
opens it in the default browser:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;``python3 desktop_launcher.py``


#### Details on desktop launcher:

Launch the frontend with:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;``python3 combined_null_4nf_frontend.py --host 127.0.0.1 --port 8767``

The frontend is found at:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;``http://127.0.0.1:8767``

The CLI accepts .txt files directly:

```
python3 combined_null_4nf_decomposer.py sample_combined_null_4nf_schema.txt
```

To build a self-contained app for the current operating system, install
PyInstaller and run the build script:

```
python3 -m pip install pyinstaller
python3 packaging/build_app.py
```

Build outputs are written to `dist/`.

- macOS builds produce a `Normaliser.app` bundle by default.
- Windows builds produce a `Normaliser.exe` executable by default.
- Linux builds produce a `Normaliser` executable by default.

PyInstaller does not cross-compile. Build each target on its own operating
system, or use the included GitHub Actions workflow.

To build all three platforms on GitHub:

1. Push the repository to GitHub.
2. Open the `Actions` tab.
3. Select `Build desktop apps`.
4. Run the workflow manually, or push a version tag such as `v1.0.0`.
5. Download the `Normaliser-macOS`, `Normaliser-Windows`, and
   `Normaliser-Linux` artifacts from the workflow run.

The workflow runs the unit tests, installs PyInstaller, builds the desktop app
on macOS, Windows, and Linux, and uploads the `dist/` folder for each platform.

For debugging a packaged app, keep a console window:

```
python3 packaging/build_app.py --console
```

For macOS distribution outside your own machine, sign and notarize the generated
`.app` with your Apple Developer certificate before sharing it.
