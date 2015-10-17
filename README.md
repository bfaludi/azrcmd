# azrcmd

Azure Blob Store command line tool to download and upload files.

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
```

## Upload files

You can upload a file easily:

```bash
$ azrcmd-put LICENSE.md wasbc://container@path/LICENSE.md
Uploading `LICENSE.md` into `path/LICENSE.md` ... OK
```

... or if the blob path's ends with `/` than it'll use the name of the file.

```bash
$ azrcmd-put LICENSE.md wasbc://container@path/
Uploading `LICENSE.md` into `path/LICENSE.md` ... OK
```

You can upload multiple files as well:

```bash
$ azrcmd-put LICENSE* wasbc://container@path/
Uploading `LICENSE.md` into `path/LICENSE.md` ... OK
Uploading `LICENSE.pdf` into `path/LICENSE.pdf` ... OK
```

If you want to upload full directories than you have to define the `--recursive` parameter.

```bash
$ azrcmd-put --recursive azurcmd/ wasbc://container@path/
Uploading `azrcmd/azrcmd/__init__.py` into `path/azrcmd/__init__.py` ... OK
Uploading `azrcmd/setup.py` into `path/setup.py` ... OK
```

Furthermore, if you want to test the function you can use the `--dryrun` parameter.

## Download files

Not implemented yet.

## List files

It'll list all blobs with the given prefix.

```bash
$ azrcmd-ls wasbc://container@path-prefix
```

## Delete files

It'll delete all blobs with the given prefix.

```bash
$ azrcmd-rm wasbc://container@path-prefix
```

## License

Copyright © 2015 Bence Faludi.

Distributed under the MIT License.
