package data

type ProjectIDs struct {
	valid   []string
	invalid []string
}

type Project struct {
	id               string
	slug             string
	title            string
	description      string
	body             string
	client_side      string
	server_side      string
	project_type     string
	game_versions    []string
	loaders          []string
	versions         []string
	invalid_versions []string
	updated          string
}

type Version struct {
	id             string
	name           string
	dependencies   []string
	parsed_deps    map[string]Version
	game_versions  []string
	version_type   string
	loaders        []string
	status         string
	date_published string
	project_id     string
	files          []string
}

type VerStack struct {
	valid   map[string]Version
	invalid map[string]Version
}

type ProjectStack struct {
	valid   map[string]Version
	invalid map[string]Version
}
