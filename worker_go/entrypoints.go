package main

import (
	"encoding/json"
	"net/http"
	"worker/data"
)

func CalculateGameVersions(w http.ResponseWriter, r *http.Request) {

	var slugs []string
	if err := json.NewDecoder(r.Body).Decode(&slugs); err != nil {
		http.Error(w, "invalid body", http.StatusBadRequest)
		return
	}

	var ProjectIDs data.ProjectIDs
	ProjectIDs.Validate(slugs, w)
}
