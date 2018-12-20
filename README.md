# undock
Small in-place template processor for unpacking static code expressions


Use this directive in your files:

`# unpack 'file' <regex>: <command>`

Json is supported as a source:

`package.json`
```json
{
  "data": {
    "packages": [

      {
        "name": "pkg1",
        "version": "0.1"
      },
      {
        "name": "pkg2",
        "version": "0"
      }
    ]
  }
}
```

`# jsonunpack 'package.json' data.packages: RUN magic {name} {version}`
 

`pipunpack` is already built-in command - for pip:

 `# pipunpack 'file'`
 
 run `main.py Dockerfile*`
 
 
 
 
 TODO: 
 1. support yaml, xml, toml
 2. New optional syntax: # for re({1}=={2}) in 'requirements.txt': RUN pip install {1}=={2} 
 3. Remove hint for file formats.