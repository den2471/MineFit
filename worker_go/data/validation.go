package data

import (
	"net/http"
	"regexp"
)

var idSlug = regexp.MustCompile(`^[A-Za-z0-9_.-]{3,64}$`)

func (p *ProjectIDs) Validate(slugs []string, w http.ResponseWriter) {

	if len(slugs) > 200 {
		http.Error(w, "too many projects", http.StatusBadRequest)
	} else if len(slugs) <= 1 {
		http.Error(w, "0 or 1 project", http.StatusBadRequest)
	}

	for _, id := range slugs {
		if idSlug.MatchString(id) {
			p.valid = append(p.valid, id)
		} else {
			p.invalid = append(p.invalid, id)
		}
	}

	if len(p.valid) == 0 {
		http.Error(w, "no valid projects found", http.StatusBadRequest)
	}
}
