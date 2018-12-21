# undock

Small in-place template processor for unpacking static code expressions.

`$ python main.py -f Docker* -i #`

All parameter are optional.

You can think of it like small template engine for configuration files with boilerplate.

For example it can be used for destructed package installation in Dockerfile to use cache effectively.

Use this directive in your files:

`# unpack 'file' <regex>: <command>`

For any regex match given command will be rendered. 
`<regex>` variables can be captured by `{varname}`(reluctant/lazy .+?) or any NAMED groups. 
This vars after used in `<command>` in the same way(environment marks ignored!):
 
`# unpack 'requirements.txt' {line}\n : RUN pip install {line}`

`# unpack 'anyfile' abcd?[a-z]?{sometoken}; : RUN pip install {sometoken}`


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

 `# pipunpack 'file': `
 
 run `main.py Dockerfile*`
 
 
 
 
 TODO: 
 1. support yaml, xml, toml
 2. New optional syntax: # for re({1}=={2}) in 'requirements.txt': RUN pip install {1}=={2} 
 3. Remove? hint for file formats.