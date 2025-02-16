import os
import shutil
import json
import pytest
from ipsframework import Framework, TaskPool


def copy_config_and_replace(infile, outfile, tmpdir, worker="hello_worker.py", portal=False):
    with open(infile, "r") as fin:
        with open(outfile, "w") as fout:
            for line in fin:
                if "hello_driver.py" in line or "hello_worker.py" in line:
                    fout.write(line.replace("${BIN_PATH}", str(tmpdir)).replace("hello_worker.py", worker))
                elif "BIN_PATH" in line:
                    fout.write(line.replace("${IPS_ROOT}/tests/helloworld", ""))
                elif line.startswith("SIM_ROOT"):
                    fout.write(f"SIM_ROOT = {tmpdir}\n")
                elif line.startswith("LOG_FILE"):
                    fout.write(line.replace("LOG_FILE = ", f"LOG_FILE = {tmpdir}/"))
                elif line.startswith("USE_PORTAL"):
                    if portal:
                        fout.write("USE_PORTAL = True\n")
                        fout.write(f"USER_W3_DIR = {tmpdir}/www\n")
                        fout.write("PORTAL_URL = http://localhost:8080\n")
                    else:
                        fout.write(line)
                else:
                    fout.write(line)


def test_helloworld(tmpdir, capfd):
    data_dir = os.path.dirname(__file__)
    copy_config_and_replace(os.path.join(data_dir, "hello_world.ips"), tmpdir.join("hello_world.ips"), tmpdir)
    shutil.copy(os.path.join(data_dir, "platform.conf"), tmpdir)
    shutil.copy(os.path.join(data_dir, "hello_driver.py"), tmpdir)
    shutil.copy(os.path.join(data_dir, "hello_worker.py"), tmpdir)

    framework = Framework(config_file_list=[os.path.join(tmpdir, "hello_world.ips")],
                          log_file_name=str(tmpdir.join('test.log')),
                          platform_file_name=os.path.join(tmpdir, "platform.conf"),
                          debug=None,
                          verbose_debug=None,
                          cmd_nodes=0,
                          cmd_ppn=0)

    assert framework.log_file_name.endswith('test.log')

    fwk_components = framework.config_manager.get_framework_components()
    assert len(fwk_components) == 1
    assert 'Hello_world_1_FWK@runspaceInitComponent@3' in fwk_components

    component_map = framework.config_manager.get_component_map()

    assert len(component_map) == 1
    assert 'Hello_world_1' in component_map
    hello_world_1 = component_map['Hello_world_1']
    assert len(hello_world_1) == 1
    assert hello_world_1[0].get_class_name() == 'HelloDriver'
    assert hello_world_1[0].get_instance_name().startswith('Hello_world_1@HelloDriver')
    assert hello_world_1[0].get_seq_num() == 1
    assert hello_world_1[0].get_serialization().startswith('Hello_world_1@HelloDriver')
    assert hello_world_1[0].get_sim_name() == 'Hello_world_1'

    framework.run()

    captured = capfd.readouterr()

    captured_out = captured.out.split('\n')
    assert captured_out[0].startswith("Starting IPS")
    assert captured_out[1] == "Created <class 'hello_driver.HelloDriver'>"
    assert captured_out[2] == "Created <class 'hello_worker.HelloWorker'>"
    assert captured_out[3] == 'HelloDriver: init'
    assert captured_out[4] == 'HelloDriver: finished worker init call'
    assert captured_out[5] == 'HelloDriver: beginning step call'
    assert captured_out[6] == 'Hello from HelloWorker'
    assert captured_out[7] == 'HelloDriver: finished worker call'
    assert captured.err == ''

    # check that portal didn't write anything since USE_PORTAL=False
    assert not os.path.exists(tmpdir.join("simulation_log"))
    assert not os.path.exists(tmpdir.join("www"))


def test_helloworld_launch_task(tmpdir, capfd):
    data_dir = os.path.dirname(__file__)
    copy_config_and_replace(os.path.join(data_dir, "hello_world.ips"), tmpdir.join("hello_world.ips"), tmpdir, worker="hello_worker_launch_task.py")
    shutil.copy(os.path.join(data_dir, "platform.conf"), tmpdir)
    shutil.copy(os.path.join(data_dir, "hello_driver.py"), tmpdir)
    shutil.copy(os.path.join(data_dir, "hello_worker_launch_task.py"), tmpdir)

    framework = Framework(config_file_list=[os.path.join(tmpdir, "hello_world.ips")],
                          log_file_name=str(tmpdir.join('test.log')),
                          platform_file_name=os.path.join(tmpdir, "platform.conf"),
                          debug=None,
                          verbose_debug=None,
                          cmd_nodes=0,
                          cmd_ppn=0)

    assert framework.log_file_name.endswith('test.log')

    fwk_components = framework.config_manager.get_framework_components()
    assert len(fwk_components) == 1
    assert 'Hello_world_1_FWK@runspaceInitComponent@3' in fwk_components

    component_map = framework.config_manager.get_component_map()

    assert len(component_map) == 1
    assert 'Hello_world_1' in component_map
    hello_world_1 = component_map['Hello_world_1']
    assert len(hello_world_1) == 1
    assert hello_world_1[0].get_class_name() == 'HelloDriver'
    assert hello_world_1[0].get_instance_name().startswith('Hello_world_1@HelloDriver')
    assert hello_world_1[0].get_seq_num() == 1
    assert hello_world_1[0].get_serialization().startswith('Hello_world_1@HelloDriver')
    assert hello_world_1[0].get_sim_name() == 'Hello_world_1'

    framework.run()

    captured = capfd.readouterr()

    captured_out = captured.out.split('\n')
    assert captured_out[0].startswith("Starting IPS")
    assert captured_out[1] == "Created <class 'hello_driver.HelloDriver'>"
    assert captured_out[2] == 'HelloDriver: init'
    assert captured_out[3] == 'HelloDriver: finished worker init call'
    assert captured_out[4] == 'HelloDriver: beginning step call'
    assert captured_out[5] == 'Hello from HelloWorker'
    assert captured_out[6] == 'Starting tasks = 0'
    assert captured_out[7] == 'Number of tasks = 1'
    assert captured_out[8] == 'wait_task ret_val = 0'
    assert captured_out[9] == 'Number of tasks = 2'
    assert captured_out[10] == 'wait_tasklist ret_val = {2: 0, 3: 0}'
    assert captured_out[11] == 'Number of tasks = 0'
    assert captured_out[12] == 'Number of tasks = 1'
    assert captured_out[13] == 'kill_task'
    assert captured_out[14] == 'Number of tasks = 0'
    assert captured_out[15] == 'Number of tasks = 2'
    assert captured_out[16] == 'kill_all_tasks'
    assert captured_out[17] == 'Number of tasks = 0'
    assert captured_out[18] == 'Timeout task 1 retval = -1'
    assert captured_out[19] == 'Timeout task 2 retval = -9'
    assert captured_out[20] == 'HelloDriver: finished worker call'
    assert captured.err == ''


def test_helloworld_task_pool(tmpdir, capfd):
    data_dir = os.path.dirname(__file__)
    copy_config_and_replace(os.path.join(data_dir, "hello_world.ips"), tmpdir.join("hello_world.ips"), tmpdir, worker="hello_worker_task_pool.py")
    shutil.copy(os.path.join(data_dir, "platform.conf"), tmpdir)
    shutil.copy(os.path.join(data_dir, "hello_driver.py"), tmpdir)
    shutil.copy(os.path.join(data_dir, "hello_worker_task_pool.py"), tmpdir)

    framework = Framework(config_file_list=[os.path.join(tmpdir, "hello_world.ips")],
                          log_file_name=str(tmpdir.join('test.log')),
                          platform_file_name=os.path.join(tmpdir, "platform.conf"),
                          debug=None,
                          verbose_debug=None,
                          cmd_nodes=0,
                          cmd_ppn=0)

    assert framework.log_file_name.endswith('test.log')

    assert len(framework.config_manager.get_framework_components()) == 1

    component_map = framework.config_manager.get_component_map()

    assert len(component_map) == 1
    assert 'Hello_world_1' in component_map
    hello_world_1 = component_map['Hello_world_1']
    assert len(hello_world_1) == 1
    assert hello_world_1[0].get_class_name() == 'HelloDriver'
    assert hello_world_1[0].get_instance_name().startswith('Hello_world_1@HelloDriver')
    assert hello_world_1[0].get_seq_num() == 1
    assert hello_world_1[0].get_serialization().startswith('Hello_world_1@HelloDriver')
    assert hello_world_1[0].get_sim_name() == 'Hello_world_1'

    framework.run()

    captured = capfd.readouterr()
    captured_out = captured.out.split('\n')

    assert captured_out[0].startswith("Starting IPS")
    assert captured_out[1] == "Created <class 'hello_driver.HelloDriver'>"
    assert captured_out[2] == "Created <class 'hello_worker_task_pool.HelloWorker'>"
    assert captured_out[3] == 'HelloDriver: init'
    assert captured_out[4] == 'HelloDriver: finished worker init call'
    assert captured_out[5] == 'HelloDriver: beginning step call'
    assert captured_out[6] == 'Hello from HelloWorker'
    assert captured_out[7] == 'ret_val =  3'

    exit_status = json.loads(captured_out[8].replace("'", '"'))
    assert len(exit_status) == 3
    for n in range(3):
        assert f'task_{n}' in exit_status
        assert exit_status[f'task_{n}'] == 0

    assert captured_out[9] == "====== Non Blocking "

    for line in range(9, len(captured_out) - 2):
        if "Nonblock_task" in captured_out[line]:
            assert captured_out[line].endswith("': 0}")

    assert captured_out[-5] == 'Active =  0 Finished =  3'

    # output from remove_task_pool
    assert captured_out[-4] == 'ret_val =  2'
    assert captured_out[-3] == "KeyError('pool')"

    assert captured_out[-2] == 'HelloDriver: finished worker call'
    assert captured.err == ''


def test_helloworld_task_pool_dask(tmpdir, capfd):
    pytest.importorskip("dask")
    pytest.importorskip("distributed")
    assert TaskPool.dask is not None

    data_dir = os.path.dirname(__file__)
    copy_config_and_replace(os.path.join(data_dir, "hello_world.ips"), tmpdir.join("hello_world.ips"), tmpdir, worker="hello_worker_task_pool_dask.py")
    shutil.copy(os.path.join(data_dir, "platform.conf"), tmpdir)
    shutil.copy(os.path.join(data_dir, "hello_driver.py"), tmpdir)
    shutil.copy(os.path.join(data_dir, "hello_worker_task_pool_dask.py"), tmpdir)

    framework = Framework(config_file_list=[os.path.join(tmpdir, "hello_world.ips")],
                          log_file_name=str(tmpdir.join('test.log')),
                          platform_file_name=os.path.join(tmpdir, "platform.conf"),
                          debug=None,
                          verbose_debug=None,
                          cmd_nodes=0,
                          cmd_ppn=0)

    framework.run()

    captured = capfd.readouterr()
    captured_out = captured.out.split('\n')

    assert captured_out[0].startswith("Starting IPS")
    assert captured_out[1] == "Created <class 'hello_driver.HelloDriver'>"
    assert captured_out[2] == "Created <class 'hello_worker_task_pool_dask.HelloWorker'>"
    assert captured_out[3] == 'HelloDriver: init'
    assert captured_out[4] == 'HelloDriver: finished worker init call'
    assert captured_out[5] == 'HelloDriver: beginning step call'
    assert captured_out[6] == 'Hello from HelloWorker'

    assert "Running setup of worker" in captured_out
    assert "Running teardown of worker" in captured_out

    assert 'ret_val =  9' in captured_out

    for duration in ("0.2", "0.4", "0.6"):
        for task in ["myFun", "myMethod"]:
            assert f'{task}({duration})' in captured_out

    exit_status = json.loads(captured_out[-3].replace("'", '"'))
    assert len(exit_status) == 9
    for n in range(3):
        for task in ["bin", "meth", "func"]:
            assert f'{task}_{n}' in exit_status
            assert exit_status[f'{task}_{n}'] == 0
