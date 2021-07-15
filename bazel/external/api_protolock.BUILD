load("@io_bazel_rules_go//go:def.bzl", "go_binary", "go_library")

licenses(["notice"])  # Apache 2

#go_binary(
#    name = "protolock",
#    deps = [
#        "@com_github_nilslice_protolock//:protolocklibcmd",
#        #"protolocklibcmd",
#        #"protolocklibroot",
#        #"protolocklibextend"
#    ],
#    visibility = ["//visibility:public"],
#)

go_binary(
    name = "protolock",
    srcs = [
        "cmd/protolock/main.go",
        "cmd/protolock/plugins.go",
    ],
    #importpath = "main",
    visibility = ["//visibility:public"],
    deps = [
        "@com_github_nilslice_protolock//:protolocklibextend",
        "@com_github_nilslice_protolock//:protolocklibroot",
    ],
)

go_library(
    name = "protolocklibextend",
    srcs = [
        "extend/plugin.go",
    ],
    importpath = "github.com/nilslice/protolock/extend",
    visibility = ["//visibility:public"],
    deps = [
        "@com_github_nilslice_protolock//:protolocklibroot",
    ],
)

go_library(
    name = "protolocklibroot",
    srcs = [
        "commit.go",
        "config.go",
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
    deps = [
        "@com_github_emicklei_proto//:proto_parsing_lib",
    ],
)
