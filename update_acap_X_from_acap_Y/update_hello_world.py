import os
import subprocess
import json
import semver
import time
import xml.etree.ElementTree as ET
import argparse

# Step 1: Create a new version of the hello_world ACAP
def update_manifest_version(manifest_path):
    """
    Update the version in the manifest.json file by incrementing the patch version.

    Args:
        manifest_path (str): Path to the manifest.json file.

    Returns:
        str: The new version number.
    """
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    current_version = manifest['acapPackageConf']['setup']['version']
    new_version = semver.bump_patch(current_version)
    manifest['acapPackageConf']['setup']['version'] = new_version

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=4)

    return new_version

# Step 2: Build the new version of hello_world
def build_hello_world(arch, app_image):
    """
    Build the new version of the hello_world ACAP using Docker.

    Args:
        arch (str): The architecture for the build (e.g., 'aarch64').
        app_image (str): The name of the Docker image to build.
    """
    # Change the current working directory to the hello-world directory
    original_dir = os.getcwd()
    os.chdir(os.path.join(original_dir, 'hello-world'))

    build_cmd = f"docker build --build-arg ARCH={arch} --tag {app_image} ."
    subprocess.run(build_cmd, shell=True, check=True)

    create_cmd = f"docker create {app_image}"
    container_id = subprocess.run(create_cmd, shell=True, check=True, capture_output=True, text=True).stdout.strip()

    cp_cmd = f"docker cp {container_id}:/opt/app ./build/{arch}"
    subprocess.run(cp_cmd, shell=True, check=True)

    # Change back to the original working directory
    os.chdir(original_dir)

# Step 3: SCP the new hello_world application to the localdata of the vapix_example
def scp_hello_world(version, device_ip, ssh_user, ssh_password):
    """
    Copy the new hello_world EAP file to the device using SCP with sshpass.

    Args:
        version (str): The new version number of the hello_world ACAP.
        device_ip (str): The IP address of the device.
        ssh_user (str): The SSH username for the device.
        ssh_password (str): The SSH password for the device.
    """
    original_dir = os.getcwd()
    print(f"original_dir: {original_dir}")

    build_dir = os.path.join(original_dir, 'hello-world', 'build', 'aarch64')
    app_dir = os.path.join(build_dir, 'app')

    if os.path.exists(app_dir):
        working_dir = app_dir
    else:
        working_dir = build_dir

    os.chdir(working_dir)
    after_ch_dir = os.getcwd()
    print(f"after_ch_dir: {after_ch_dir}")

    version_with_underscores = version.replace('.', '_')
    src_path = os.path.join(working_dir, f"hello_world_{version_with_underscores}_aarch64.eap")
    subprocess.run('ls -la', shell=True, check=True)
    print(f"src_path: {src_path}")

    dest_path = f"{ssh_user}@{device_ip}:/usr/local/packages/vapix_example/localdata/hello_world.eap"
    scp_cmd = f"sshpass -p '{ssh_password}' scp {src_path} {dest_path}"
    print(f"scp_cmd: {scp_cmd}")

    subprocess.run(scp_cmd, shell=True, check=True)
    os.chdir(original_dir)

# Step 4: Start the vapix_example ACAP
def start_vapix_example(device_ip, device_user, device_password):
    """
    Start the vapix_example ACAP on the device.

    Args:
        device_ip (str): The IP address of the device.
        device_user (str): The username for the device.
        device_password (str): The password for the device.
    """
    start_cmd = f"curl --anyauth -u {device_user}:{device_password} 'http://{device_ip}/axis-cgi/applications/control.cgi?action=start&package=vapix_example'"
    print(f"start_cmd: {start_cmd}")
    subprocess.run(start_cmd, shell=True, check=True)

# Step 5: Verify the version number was updated
def verify_version(device_ip, device_user, device_password, expected_version):
    """
    Verify that the hello_world ACAP was updated to the expected version.

    Args:
        device_ip (str): The IP address of the device.
        device_user (str): The username for the device.
        device_password (str): The password for the device.
        expected_version (str): The expected version number of the hello_world ACAP.
    """
    # Wait for 3 seconds to allow the updated version to be reflected
    time.sleep(3)

    list_cmd = f"curl --anyauth -u {device_user}:{device_password} 'http://{device_ip}/axis-cgi/applications/list.cgi'"
    output = subprocess.run(list_cmd, shell=True, check=True, capture_output=True, text=True).stdout

    # Parse the XML output
    root = ET.fromstring(output)

    # Find the hello_world application element
    hello_world_app = next((app for app in root.findall('application') if app.get('Name') == 'hello_world'), None)

    if hello_world_app is not None:
        installed_version = hello_world_app.get('Version')
        if installed_version == expected_version:
            print(f"hello_world version {expected_version} installed successfully!")
        else:
            print(f"Error: Expected version {expected_version} but found {installed_version}")
    else:
        print("Error: hello_world application not found in the output.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update the hello_world ACAP on a device.")
    parser.add_argument("--iterations", type=int, default=1, help="Number of times to run the update process")
    args = parser.parse_args()

    device_ip = "172.25.74.66"
    ssh_user = "acap-vapix_example"
    ssh_password = "pass"
    device_user = "root"
    device_password = "pass"
    arch = "aarch64"
    app_image = "hello_world:latest"

    manifest_path = os.path.join("hello-world", "app", "manifest.json")

    for _ in range(args.iterations):
        new_version = update_manifest_version(manifest_path)
        build_hello_world(arch, app_image)
        scp_hello_world(new_version, device_ip, ssh_user, ssh_password)
        start_vapix_example(device_ip, device_user, device_password)
        verify_version(device_ip, device_user, device_password, new_version)
