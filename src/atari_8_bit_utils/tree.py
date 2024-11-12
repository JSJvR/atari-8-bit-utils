atr_tree = {
    "name": "Root",
    "type": "Selector",
    "children": [
        {
            "name": "Global",
            "type": "Selector",
            "children": [
                "ForceQuit",
                "DefaultConfig",
                "ApplyConfig"
            ]
        },
        {
            "name": "Outgoing",
            "type": "Selector",
            "children": [
                "ExtractATR",
                "DeleteUTF8",
                {
                    "name": "ProcessOutput",
                    "type": "Selector",
                    "children": [
                        {
                            "name": "AutoCommit",
                            "type": "Sequence",
                            "children": [
                                "WriteUTF8",
                                {
                                    "name": "GitOut",
                                    "type": "Sequence",
                                    "children": [
                                        "PreCommit",
                                        "Commit",
                                        "PostCommit"
                                    ]
                                }
                            ]
                        },
                        {
                            "ref": "WriteUTF8"
                        }
                    ]
                },
                {
                    "name": "ConditionalCommit",
                    "type": "Selector",
                    "children": [
                        {
                            "ref": "GitOut"
                        }
                    ]
                }
            ]
        },
        "Incoming",
        "Iterate",
        "Wait"
    ]
}
