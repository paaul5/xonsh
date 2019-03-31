import os
import tempfile
import pytest

from xonsh.xoreutils import _which
from xonsh.xoreutils import uptime
from xonsh.xoreutils import cat
from xonsh.tools import ON_WINDOWS


class TestWhich:
    # Tests for the _whichgen function which is the only thing we
    # use from the _which.py module.
    def setup(self):
        # Setup two folders with some test files.
        self.testdirs = [tempfile.TemporaryDirectory(), tempfile.TemporaryDirectory()]
        if ON_WINDOWS:
            self.testapps = ["whichtestapp1.exe", "whichtestapp2.wta"]
            self.exts = [".EXE"]
        else:
            self.testapps = ["whichtestapp1"]
            self.exts = None
        for app in self.testapps:
            for d in self.testdirs:
                path = os.path.join(d.name, app)
                with open(path, "wb") as f:
                    f.write(b"")
                os.chmod(path, 0o755)

    def teardown_module(self):
        for d in self.testdirs:
            d.cleanup()

    def test_whichgen(self):
        testdir = self.testdirs[0].name
        arg = "whichtestapp1"
        matches = list(_which.whichgen(arg, path=[testdir], exts=self.exts))
        assert len(matches) == 1
        assert self._file_match(matches[0][0], os.path.join(testdir, arg))

    def test_whichgen_failure(self):
        testdir = self.testdirs[0].name
        arg = "not_a_file"
        matches = list(_which.whichgen(arg, path=[testdir], exts=self.exts))
        assert len(matches) == 0

    def test_whichgen_verbose(self):
        testdir = self.testdirs[0].name
        arg = "whichtestapp1"
        matches = list(
            _which.whichgen(arg, path=[testdir], exts=self.exts, verbose=True)
        )
        assert len(matches) == 1
        match, from_where = matches[0]
        assert self._file_match(match, os.path.join(testdir, arg))
        assert from_where == "from given path element 0"

    def test_whichgen_multiple(self):
        testdir0 = self.testdirs[0].name
        testdir1 = self.testdirs[1].name
        arg = "whichtestapp1"
        matches = list(_which.whichgen(arg, path=[testdir0, testdir1], exts=self.exts))
        assert len(matches) == 2
        assert self._file_match(matches[0][0], os.path.join(testdir0, arg))
        assert self._file_match(matches[1][0], os.path.join(testdir1, arg))

    if ON_WINDOWS:

        def test_whichgen_ext_failure(self):
            testdir = self.testdirs[0].name
            arg = "whichtestapp2"
            matches = list(_which.whichgen(arg, path=[testdir], exts=self.exts))
            assert len(matches) == 0

        def test_whichgen_ext_success(self):
            testdir = self.testdirs[0].name
            arg = "whichtestapp2"
            matches = list(_which.whichgen(arg, path=[testdir], exts=[".wta"]))
            assert len(matches) == 1
            assert self._file_match(matches[0][0], os.path.join(testdir, arg))

    def _file_match(self, path1, path2):
        if ON_WINDOWS:
            path1 = os.path.normpath(os.path.normcase(path1))
            path2 = os.path.normpath(os.path.normcase(path2))
            path1 = os.path.splitext(path1)[0]
            path2 = os.path.splitext(path2)[0]
            return path1 == path2
        else:
            return os.path.samefile(path1, path2)


def test_uptime():
    up = uptime.uptime()
    assert up is not None
    assert up > 0.0


def test_boottime():
    bt = uptime.boottime()
    assert bt is not None
    assert bt > 0.0
    assert uptime._BOOTTIME is not None
    assert uptime._BOOTTIME > 0.0


class TestCat:
    tempfile = None

    def setup_method(self, _method):
        import tempfile
        tmpfile = tempfile.mkstemp()
        self.tempfile = tmpfile[1]

    def teardown_method(self, _method):
        os.remove(self.tempfile)

    def test_cat_single_file_work_exist_content(self):
        import io

        content = "this is a content\nfor testing xoreutil's cat"
        with open(self.tempfile, "w") as f:
            f.write(content)

        stdin = io.StringIO()
        stdout_buf = io.BytesIO()
        stderr_buf = io.BytesIO()
        stdout = io.TextIOWrapper(stdout_buf)
        stderr = io.TextIOWrapper(stderr_buf)
        opts = cat._cat_parse_args([])
        cat._cat_single_file(opts, self.tempfile, stdin, stdout, stderr)
        stdout.flush()
        stderr.flush()
        assert stdout_buf.getvalue() == bytes(content, "utf-8")
        assert stderr_buf.getvalue() == b''

    def test_cat_empty_file(self):
        import io

        with open(self.tempfile, "w") as f:
            f.write("")

        stdin = io.StringIO()
        stdout_buf = io.BytesIO()
        stderr_buf = io.BytesIO()
        stdout = io.TextIOWrapper(stdout_buf)
        stderr = io.TextIOWrapper(stderr_buf)
        opts = cat._cat_parse_args([])
        cat._cat_single_file(opts, self.tempfile, stdin, stdout, stderr)
        stdout.flush()
        stderr.flush()
        assert stdout_buf.getvalue() == b''
        assert stderr_buf.getvalue() == b''
