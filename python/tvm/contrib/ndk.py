# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Util to invoke NDK compiler toolchain."""
# pylint: disable=invalid-name
from __future__ import absolute_import as _abs

import subprocess
import os
from .._ffi.base import py_str
from .cc import get_target_by_dump_machine


def create_shared(output, objects, options=None):
    """Create shared library.

    Parameters
    ----------
    output : str
        The target shared library.

    objects : list
        List of object files.

    options : list of str, optional
        The additional options.
    """
    if "TVM_NDK_CC" not in os.environ:
        raise RuntimeError(
            "Require environment variable TVM_NDK_CC" " to be the NDK standalone compiler"
        )
    compiler = os.environ["TVM_NDK_CC"]
    cmd = [compiler]
    cmd += ["-o", output]

    if isinstance(objects, str):
        cmd += [objects]
    else:
        cmd += objects

    options = options if options else ["-shared", "-fPIC", "-lm"]
    cmd += options

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out, _) = proc.communicate()

    if proc.returncode != 0:
        msg = "Compilation error:\n"
        msg += py_str(out)
        raise RuntimeError(msg)


# assign output format
create_shared.output_format = "so"
create_shared.get_target_triple = (
    get_target_by_dump_machine(os.environ["TVM_NDK_CC"]) if "TVM_NDK_CC" in os.environ else None
)


def create_staticlib(output, objects):
    """Create static library:

    Parameters
    ----------
    output : str
        The target static library.

    objects : list
        List of object files.
    """
    if "TVM_NDK_CC" not in os.environ:
        raise RuntimeError(
            "Require environment variable TVM_NDK_CC" " to be the NDK standalone compiler"
        )
    output_name = os.path.basename(output)
    tmp_output = os.path.join(os.path.dirname(output), "lib" + output_name)

    compiler = os.environ["TVM_NDK_CC"]
    base_path = os.path.dirname(compiler)
    ar_path = os.path.join(base_path, "llvm-ar")
    cmd = [ar_path]
    cmd += ["qcs", tmp_output]
    cmd += objects

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out, _) = proc.communicate()
    if proc.returncode != 0:
        msg = "AR error:\n"
        msg += py_str(out)
        msg += "\nCommand line: " + " ".join(cmd)
        raise RuntimeError(msg)

    ranlib_path = os.path.join(base_path, "llvm-ranlib")
    cmd = [ranlib_path]
    cmd += [tmp_output]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out, _) = proc.communicate()
    if proc.returncode != 0:
        msg = "Ranlib error:\n"
        msg += py_str(out)
        msg += "\nCommand line: " + " ".join(cmd)
        raise RuntimeError(msg)

    proc = subprocess.Popen(
        ["mv", tmp_output, output], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    (out, _) = proc.communicate()
    if proc.returncode != 0:
        msg = "Move error:\n"
        msg += py_str(out)
        msg += "\nCommand line: " + f"mv {tmp_output} {output}"
        raise RuntimeError(msg)


create_staticlib.output_format = "a"
