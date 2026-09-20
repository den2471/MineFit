package main

import (
	"log"
	"net/http"
	"worker/config"
)

var cfg *config.Config

func init() {
	var err error
	cfg, err = config.Load()
	if err != nil {
		log.Fatal("Can't load config variables")
	}

}

func main() {
	http.HandleFunc("/game_versions", CalculateGameVersions)
}
