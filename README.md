# jdhbackend
backend for our Journal of Digital History

## development (with pipenv)

First of all, make sure that pipenvlock and requirements.txt are synced, then
start the JDH django apps using make.

```
pipenv install -r requirements.txt

make run-dev
```

### SEO configuration in development
THe django app `jdhseo` needs a JDHSEO_PROXY_HOST env variable in the full form
**without the trailing slash** like `https://local-proxy-domain-name`.
Plain `http` protocol can also be used.
The domain name provided should correctly handle the `/proxy-githubusercontent`
path.
By default this value is set to `https://journalofdigitalhistory.org`
