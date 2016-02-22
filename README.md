# azrcmd

[![Build Status](https://travis-ci.org/bfaludi/azrcmd.svg)](https://travis-ci.org/bfaludi/azrcmd)
![Downloads](https://img.shields.io/pypi/dm/azrcmd.svg)
![Version](https://img.shields.io/pypi/v/azrcmd.svg)
![License](https://img.shields.io/pypi/l/azrcmd.svg)

Azure Blob Store command line tool to download and upload files. It works in Python **2.7 & 3.3+**.
This package was crafted for using Azure Blob Store in **Linux** or **OSX**! Windows is not supported. 
It was heavily inspired by [s3cmd](http://s3tools.org/s3cmd).

## Installation

You can install easily with `pip`.

```bash
$ pip install azrcmd
```

**Note**: You won't be able to install it with `easy_install` because of the incompatibility between `setuptools` and `azure` libraries. 

Create your configuration file as a bash script or put this information on your `.bash_profile`.

```sh
export AZURE_STORAGE_ACCOUNT=""
export AZURE_STORAGE_ACCESS_KEY=""
export AZURE_STORAGE_MAX_CONNECTIONS=5
```

## Usage

#### Upload files

You can upload a file easily:

```bash
$ azrcmd-put filename wasbc://container/path/filename
$ azrcmd-put filename wasbc://container/path/
```

Of course, you can upload multiple files with a single command:

```bash
$ azrcmd-put filepart* wasbc://container/path/
```

If you want to upload full directories than you have to define the `--recursive` parameter.

```bash
$ azrcmd-put --recursive dirname/ wasbc://container/path/dirname/
```

Furthermore, if you want to test the function you can use the `--dryrun` parameter.

#### Download files

Download a single file with

```bash
$ azrcmd-get wasbc://container/path/filename filename
$ azrcmd-get wasbc://container/path/filename dirname/
```

Download files and directories with the `--prefix` parameter.

```bash
$ azrcmd-get --prefix wasbc://container/path-prefix dirname/
$ azrcmd-get --prefix wasbc://container/path-prefix/ dirname/
```

It always override the already existing files! If you want to turn off this behaviour, please use the `--skip_existing` parameter.
Of course, if you only want to download the new or changed blobs than you'd use the `--sync` attribute.
You can test the methods with the `--dryrun` parameter.

#### List files

List all blobs with the given prefix.

```bash
$ azrcmd-ls wasbc://container/path-prefix
```

#### Delete files

Delete a single blob with the following command:

```bash
$ azrcmd-rm wasbc://container/path/filename
```

or multiple blobs with a prefix:

```bash
$ azrcmd-rm --prefix wasbc://container/path-prefix
```

You can test the methods with the `--dryrun` parameter.

## What's next?

- Add `--sync` parameter to do not upload or download unchanged files.
- Symlink support (ignoring circles).
- etc.

## License

Copyright © 2015 Bence Faludi.

Distributed under the MIT License.
