import sys, os, pathlib, json, shutil, zipfile
argv = sys.argv[1:]
version = "1.0.0"
def printHelp():
    print( f"J2MEBuild v{version}.\n"+
            "Available subcommands:\n"+
            "help -> show this.\n"
            "init -> create project. You will be asked for some values.\n"+
            "build <path> -> build project at specific name in current directory." )
def getValue(what, can_be_empty, default_value = ""):
    default = f"[{default_value}]" if len(default_value) > 0 else ""
    value = input(f"Input {what}{default}: ")
    if can_be_empty or len(value) > 0:
        if len(value) > 0:
            return value
        else:
            return default_value
    else:
        return getValue(what, can_be_empty, default_value)
if len(argv) == 0:
    printHelp()
    sys.exit(0)
if argv[0] == "init":
    print(f"J2MEBuild v{version}.")
    project_name = getValue("project name (better should not contain spaces)", False)
    project_version = getValue("project version", True, "1.0")
    project_vendor = getValue("project vendor (author)", True, "Unknown")
    project_path = getValue("project path(better use paths only in current directory)", True, os.path.join(str(pathlib.Path().absolute()), project_name))
    project_main_class = getValue("project main class", True, "Main")
    data = {
        "project_name": project_name,
        "project_version": project_version,
        "project_vendor": project_vendor,
        "project_main_class": project_main_class
    }
    data_json = json.dumps(data, indent=4)
    try:
        os.mkdir(project_path)
        os.mkdir(os.path.join(project_path, "src"))
        os.mkdir(os.path.join(project_path, "build"))
        os.mkdir(os.path.join(project_path, "dist"))
    except FileExistsError:
        pass
    data_file_path = os.path.join(project_path, "project.json")
    data_file = open(data_file_path, "w")
    data_file.write(data_json)
    data_file.close()
    print(f"Wrote to {data_file_path}:")
    print(data_json)
elif argv[0] == "build":
    if len(argv) < 2:
        print( f"J2MEBuild v{version}.\n"+
                "Specify project name in current directory." )
        sys.exit(1)
    project_name = " ".join(argv[1:])
    project_path = os.path.join(str(pathlib.Path().absolute()), project_name)
    if not os.path.isdir(project_path):
        print("There is no such project.")
        sys.exit(1)
    data_file = None
    try:
        data_file = open(os.path.join(project_path, "project.json"), "r")
    except Exception as e:
        print("project.json file does not exist or is unreadable.")
        sys.exit(1)
    data = None
    try:
        data = json.loads(data_file.read())
    except Exception:
        print("project.json file is not a valid JSON.")
        sys.exit(1)
    if (not ("project_name" in data)) or (not ("project_version" in data)) or (not ("project_vendor" in data)) or (not ("project_main_class" in data)):
        print("One or more properties(project_name, project_version, project_vendor or project_main_class) doesn't exist.")
        sys.exit(1)
    print("Compiling(no error handling for now :sad:)...")
    shutil.rmtree(os.path.join(project_path, "build"))
    os.mkdir(os.path.join(project_path, "build"))
    api_path = os.path.join((os.sep).join(__file__.split(os.sep)[:-1]), os.path.join("data", os.path.join("midpapi", "api.jar")))
    source_path = os.path.join(project_path, "src")
    source_files = os.path.join(source_path, "*.java")
    output_path = os.path.join(project_path, "build")
    command = f"javac -cp {api_path} -target 1.1 -source 1.3 -nowarn -encoding UTF-8 {source_files} -d {output_path}"
    os.system(command)
    print("Creating manifest.")
    manifest_file = open(os.path.join(output_path, "MANIFEST.MF"), "w")
    midlet_vendor = data["project_vendor"]
    midlet_version = data["project_version"]
    midlet_name = data["project_name"]
    midlet_main_class = data["project_main_class"]
    manifest_file.write(
        "Manifest-Version: 1.0\n"+
        "Ant-Version: Apache Ant 1.9.4\n"+
        "Created-By: 1.8.0_25-b18 (Oracle Corporation)\n"+
        f"MIDlet-1: {midlet_main_class},,{midlet_main_class}\n"+
        f"MIDlet-Vendor: {midlet_vendor}\n"+
        f"MIDlet-Version: {midlet_version}\n"+
        f"MIDlet-Name: {midlet_name}\n"+
        "MicroEdition-Configuration: CLDC-1.1\n"+
        "MicroEdition-Profile: MIDP-2.0"
    )
    manifest_file.close()
    print("Creating initial JAR.")
    jar_path = os.path.join(output_path, "temp.jar")
    outjar_path = os.path.join(output_path, f"{midlet_name}.jar")
    open(jar_path, "w").close()
    with zipfile.ZipFile(jar_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(os.path.join(output_path, "MANIFEST.MF"), arcname=os.path.join("META-INF", "MANIFEST.MF"))
        for address, dirs, files in os.walk(output_path):
            for file in files:
                if file != "MANIFEST.MF" and file != "temp.jar":
                    zf.write(os.path.join(address, file), arcname=os.path.join((os.sep).join(dirs), file))
    print("Running proguard...")
    proguard_path = os.path.join((os.sep).join(__file__.split(os.sep)[:-1]), os.path.join("data", os.path.join("proguard", "proguard.jar")))
    cldcapi11_path = os.path.join((os.sep).join(__file__.split(os.sep)[:-1]), os.path.join("data", os.path.join("proguard", "cldcapi11.jar")))
    midpapi20_path = os.path.join((os.sep).join(__file__.split(os.sep)[:-1]), os.path.join("data", os.path.join("proguard", "midpapi20.jar")))
    proguard_command = f"java -jar {proguard_path} -injars {jar_path} -outjars {outjar_path} -libraryjars {cldcapi11_path} -libraryjars {midpapi20_path} -microedition -keep \"public class * extends javax.microedition.midlet.MIDlet\" -dontoptimize -dontshrink"
    os.system(proguard_command)
    shutil.rmtree(os.path.join(project_path, "dist"))
    os.mkdir(os.path.join(project_path, "dist"))
    print("Copying...")
    shutil.copyfile(outjar_path, os.path.join(os.path.join(project_path, "dist"), f"{midlet_name}.jar"))
    print("Cleaning...")
    shutil.rmtree(os.path.join(project_path, "build"))
    os.mkdir(os.path.join(project_path, "build"))
    print("Done.")
elif argv[0] == "help":
    printHelp()
else:
    print( f"J2MEBuild v{version}.\n"+
            "Subcommand not found. Run with \"help\" argument to get help." )
    sys.exit(1)