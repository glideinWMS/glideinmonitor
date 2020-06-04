# GlideinMonitor Filtering

Depending on displaying .out, .err, condor logs, etc. - there may be restrictions on what kind of data can be shared publicly.  Filtering allows factory operations to remove and replace data that needs to be redacted.

When the index system creates long term archives of the .out/.err files, it generates two separate archives.  The first archive it generates is of the original files with no modification, and has the prefix `original_` and ends in `.tar.gz`.  The second archive is one that has had its files run through filters (if any) that may have been in place, and has the prefix `filter_` and ends in `.tar.gz`.

The GlideinMonitor Web Frontend has an option to provide users with either the original archive or the filtered archive depending on what is selected from the configuration file.  This is helpful for users who may not permissions to view the original logs but still want to debug their Glideins as they run.

GlideinMonitor can also save the original archives and filtered archives in totally separate directory trees.  This allows for easy permission of these directories as needed. 

## Filter Configuration

Any number of filters may be added to the configuration file like below,

```json
  "filters": [
    {
      "name": "f1",
      "description": "Replaces factory names",
      "type": "whole",
      "exe": "path_to_filterF1",
      "timeout": 120
    },
    {
      "name": "f2",
      "description": "Redacts Condor XML Description",
      "type": "unpacked",
      "exe": "path_to_filterF2",
      "timeout": 0
    }
  ],
```

Here there are two filters in this example.  Each filter has a unique name, a type, a path to the filter's executable location, and a timeout.  

The jobs will be filtered in the sequence of the filters listed in the configuration file.  There is a additional process that unpacks and packs depending on switched to and from a type of the filter.  It is recommended for performance, but not required, that the same type of filters be next to each other in the sequence.

### Filter Name & Description Config

Each filter has a unique name from the other filters.  The filter's name is used in the back end to create a directory - so choose a name that can be the name of a directory.

Filters can also be given a description that is purely for documentation purposes.

### Filter Type Config

Each filter has a type, which tells the indexer which type of files to provide the filter.  `.out` and `.err` files may have hashed/compressed data within them such as condor logs.  Depending on the filter, it may want to filter out just the raw `.out` and `.err` files themselves (choose `whole`).  A filter also may want to filter out these files and/or the unhashed/uncompressed data within them (choose `unpacked`).

The types of filters are:

- `whole` - The filter will just be given the raw files, such as just `.out` and `.err`
- `unpacked` - The filter will be given the raw files, with it's unhashed/uncompressed data removed, and also unhashed/uncompressed as files as well.  Example files could include `.out`, `.err`, `.err.xml_desc`, `.err.startd`, etc.

*Note for the unpacked type*: If the `unpacked` type is chosen for the filter, the raw base file may include placeholders such as `[.xml_desc.err]`, this placeholder is made of up the uncompressed/unhashed data's file name in between brackets.  These placeholders should not be removed/modified (unless the filter is designed to remove those sections altogether), instead, **modify the actual file it points to**.

### Filter Executable Location Config

The `exe` configuration is the absolute path to the filter.  The actual path should be structured in a way that is processable to the system that the index system is running on (Windows & Linux systems use a different path structure, use the appropriate structure).  This is a path that should point to an executable file which is the filter itself.  The filter should support the following arguments,

```
> filter_config_exe -i "in_path" -o "out_path"
```

The `in_path` is a directory that the filter should read/copy/modify and eventually **delete** all job files it finds.  The `in_path` may have many jobs (like `6eac2140-a59d-11ea-a174-a85e45e1c2a5.out` and `6eac2140-a59d-11ea-a174-a85e45e1c2a5.err`) of many types (like ending in `.err`, `.out`, `.log.err`, `xml_desc.err`, etc.).  

The filter can determine the filetype of a file by looking at the extension.  The filter can determine files of the same job by looking at the name.  For example, `6eac2140-a59d-11ea-a174-a85e45e1c2a5.err` and `6eac2140-a59d-11ea-a174-a85e45e1c2a5.out` are of the same job since they are both named `6eac2140-a59d-11ea-a174-a85e45e1c2a5` with different extensions.  The names are purely random UUID strings and have nothing to do with the job ID or contents of the file.

The filter should delete the file in the `in_path` once it is done processing it.  It should place the processed file **with the same filename** in the `out_path`.  It should also move/process every file in the directory, even if the filter doesn't support its file type.  For instance, in the future, in addition to `.out` and `.err`, there may be a `.log` as well.  If the filter does not know how to process it, either move the file as is or create a file with the name that is empty.

The indexer will continue to place job files in the `in_path`, even while the filter may be running.  It will continuously check to see if a filter completed a job/batch of jobs by checking to see if all the job files have been removed from the `in_path` directory and added to the `out_path` directory.

So, when the indexer has finished adding all the files to the `in_path` and the filter has completed it's work - the `in_path` directory should be empty and the `out_path` should have every file of the same name that was found in the `in_path`.

*Note*: Once a file is placed in the `out_path`, it should never be modified or even checked for existence again.  The indexer will move files with no lock on them from the `out_path` for further processing immediately.

In short, a filter should be set up to perform a loop of the following,

- List out all files in the `in_path` directory (a snapshot of all the files currently in the directory)
    - Modify a found job file and move them to the `out_path` once processed.  Make sure once sent/moved to the `out_path` folder, the file in the `in_path` folder is removed.
- Repeat a directory listing - this will find any new files since the previous snapshot (optional, but recommended for performance).  If no new files have been found, the filter should terminate.

*Note:* If the "repeat directory listing" feature is not added and if the indexer knows that the filter has terminated while there are still files in the `in_path` directory, it will start the filter the same way it has done before - expecting the filter to process those files and eventually delete them.

*Note:*  Providing a return code other than 0 will tell the indexer to write an error to the log and terminate all filters (thus not creating a filter archive altogether).

### Filter Timeout Config

A timeout (in seconds) can be configured that should represent the max time a filter should take to process a batch of job files.  A timeout of `0` can be configured to disable this feature for a given filter which will allow it to run forever.  Each filter has it's own timeout starting point, and starts when all the job files has reached its individual `in_path` folder (when the timeout starts for a filter, it means no more files will be placed in it's `in_path` folder).

There are two events will a timeout can cause a failure for filtering:

- Not terminating on time when reaching the end of the timeout period
- Already being terminated even though there are still files in the `in_path` folder.  Again, if a filter terminates and new files end up in the `in_path` folder, the indexer will start another instance of the filter's executable.  If the filter continuously terminates while leaving files still in the `in_path` folder, then this is a possible event where a timeout will be reached.

A timeout failure for an individual filter causes the following:

- Any files still in the `in_path` folder for that filter will not be archived since they are not fully filtered
- An error is written to the log stating the filter's name with a timeout error
- Any files that made it to the `out_path` folder will continue for processing by other filters

*Note:*  Timeout periods for multiple filters don't all start at the same time.  Instead, the indexer goes on a one by one basis.  For example, let's assume there are three filters in consecutive order in the config file,

| **Name** | **Timeout Period** |
| -------- | ------------------ |
| FilterA  | 30                 |
| FilterB  | 120                |
| FilterC  | 40                 |

FilterA's is the first timeout to begin, which will run for 30 seconds.  Once FilterA has completed processing all files or it's timeout has caused it to terminate, then and only then will FilterB's time begin. 

The worst case runtime for the entire filtering process, which again starts when the indexer has added all possible files to the FilterA's folder, would be 190 (30 + 120 + 40)

## Extra Notes

For the indexer to work correctly, the filter should be designed in a way that no file will be deleted from the `in_path` and not present in the `out_path` at the same time.  The filter should use either two methods,

- Modify a job file in place in the `in_path` directory and then move the file to the `out_path` directory when completely done processing that file.
- Create a new file in the `out_path` with the same name and write data to it.  Once it has completed writing data to it and the lock has been removed, then delete the file in the `in_path`.

----

Jobs files will be moved into filter's `in_path` directory at any time, meaning, a filter might be given the `.err` file first and later on be given the `.out` file.  If a filter requires both files present before continuing with processing, skip that file leaving it in the `in_path` directory and terminate.  The indexer will at some point start the filter where both files are present.
