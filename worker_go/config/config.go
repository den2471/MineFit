package config

import "github.com/caarlos0/env/v11"

type Config struct {
	Local    Local
	External External
}

type Local struct {
	Debug bool `env:"DEBUG" envDefault:"false"`
}

type External struct {
	CacheHost string `env:"CACHEHOST,required"`
	CacheUser string `env:"CACHEUSER,required"`
	CachePass string `env:"CACHEPASS,required"`
	CacheTTL  int    `env:"CACHETTL" default:"900"`

	DbHost string `env:"DBHOST,required"`
	DbUser string `env:"DBUSER,required"`
	DbPass string `env:"DBPASS,required"`

	ApiProjectsEndpoint string `env:"API_PROJECTS_ENDPOINT,required"`
	ApiVersionsEndpoint string `env:"API_VERSIONS_ENDPOINT,required"`
}

func Load() (*Config, error) {
	cfg := &Config{}
	if err := env.Parse(cfg); err != nil {
		return nil, err
	}
	return cfg, nil
}
