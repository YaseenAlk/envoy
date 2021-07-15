load("@io_bazel_rules_go//go:def.bzl", "go_binary", "go_library")

licenses(["notice"])  # Apache 2

go_binary(
    name = "protolock",
    embed = [
        "protolocklib",
    ],
    visibility = ["//visibility:public"],
)

go_library(
    name = "protolocklib",
    srcs = [
        "cmd/protolock/main.go",
        "cmd/protolock/plugins.go",
        "commit.go",
        "config.go",
        "extend/plugin.go",
        "hints.go",
        "init.go",
        "parse.go",
        "protopath.go",
        "report.go",
        "rules.go",
        "status.go",
        "uptodate.go",
    ],
    importpath = "github.com/nilslice/protolock",
    visibility = ["//visibility:public"],
)
