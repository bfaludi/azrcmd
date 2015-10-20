# azrcmd

Azure Blob Store command line tool to download and upload files.

**UNDER DEVELOPMENT!**

TO-DOs:
- Tests are missing to validate the input/output paths.
- Check with large files.
- Add configuration to modify `max_connections` number.

## Installation

You can install easily.

```bash
$ git clone git@github.com:bfaludi/azrcmd.git
$ cd azrcmd
$ python setup.py install
```

Create your configuration file as a bash script or put this information on your `.bash_profile`.

```sh
export AZURE_STORAGE_ACCOUNT=""
export AZURE_STORAGE_ACCESS_KEY=""
export AZURE_STORAGE_MAX_CONNECTIONS=5
```

## Upload files

You can upload a file easily:

```bash
$ azrcmd-put filename wasbc://container@path/filename
$ azrcmd-put filename wasbc://container@path/
```

Of course, you can upload multiple files with a single command:

```bash
$ azrcmd-put filepart* wasbc://container@path/
```

If you want to upload full directories than you have to define the `--recursive` parameter.

```bash
$ azrcmd-put --recursive dirname/ wasbc://container@path/dirname/
```

Furthermore, if you want to test the function you can use the `--dryrun` parameter.

## Download files

Download a single file with

```bash
$ azrcmd-get wasbc://container@path/filename filename
$ azrcmd-get wasbc://container@path/filename dirname/
```

Download files and directories with the `--prefix` parameter.

```bash
$ azrcmd-get --prefix wasbc://container@path-prefix dirname/
```

You can test the methods with the `--dryrun` parameter.

## List files

List all blobs with the given prefix.

```bash
$ azrcmd-ls wasbc://container@path-prefix
```

## Delete files

Delete a single blob with the following command:

```bash
$ azrcmd-rm wasbc://container@path/filename
```

or multiple blobs with a prefix:

```bash
$ azrcmd-rm --prefix wasbc://container@path-prefix
```

You can test the methods with the `--dryrun` parameter.

## License

Copyright © 2015 Bence Faludi.

Distributed under the MIT License.
