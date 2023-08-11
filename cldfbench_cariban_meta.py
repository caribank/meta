import pathlib
import pandas as pd
from cldfbench import Dataset as BaseDataset
from writio import load, dump
import pybtex
from pycldf.sources import Source
from Bio import Phylo
from io import StringIO


import logging
import colorlog

log = logging.getLogger(__name__)
log.propagate = True
log.setLevel(logging.DEBUG)
handler = colorlog.StreamHandler(None)
handler.setFormatter(
    colorlog.ColoredFormatter("%(log_color)s%(levelname)-7s%(reset)s %(message)s")
)
log.addHandler(handler)


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "cariban_meta"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        from cldfbench import CLDFSpec

        return CLDFSpec(
            dir=self.cldf_dir, module="StructureDataset", metadata_fname="metadata.json"
        )

    def cmd_download(self, args):
        """
        Download files to the raw/ directory. You can use helpers methods of `self.raw_dir`, e.g.

        >>> self.raw_dir.download(url, fname)
        """
        pass

    def cmd_makecldf(self, args):
        from cldfbench.catalogs import pyglottolog, Glottolog

        lgs = pd.read_csv(
            "raw/cariban_language_list.csv",
            dtype={"Latitude": "float", "Longitude": "float"},
        )
        lgs = lgs.fillna("")

        def get_lg(lgid):
            return lgs[lgs["ID"]==lgid].iloc[0]

        def get_parent(tree, child_clade):
            node_path = tree.get_path(child_clade)
            return node_path[-2]

        tree = load("raw/tree.nwk").replace("\n", "").replace(" ", "")
        mod_tree = Phylo.read(
            StringIO(tree),
            format="newick",
        )
        stop = False
        for item in mod_tree.get_terminals():
            ldata = get_lg(item.name)
            if ldata["Dialect_Of"]:
                if stop:
                    item.name = ldata["Dialect_Of"]
                    stop = False
                else:
                    # log.debug(f"Pruning {item.name}")
                    parent = get_parent(mod_tree, item)
                    res = mod_tree.prune(item)
                    if res != parent:
                        stop = True
        new_tree = StringIO()
        Phylo.write(mod_tree, new_tree, plain=True, format="newick")
        min_tree = new_tree.getvalue().strip("\n")
        print(min_tree)

        glottolog = pyglottolog.Glottolog(Glottolog.from_config().repo.working_dir)

        args.writer.cldf.add_component("LanguageTable")
        args.writer.cldf.add_component("ParameterTable")
        args.writer.cldf.remove_columns("LanguageTable", "Macroarea", "ISO639P3code")
        args.writer.cldf.add_columns(
            "LanguageTable",
            {
                "name": "IPA",
                "datatype": "string",
                "dc:description": "The language name in a phonemic transcription",
                "required": False,
            },
            {
                "name": "Alternative_Names",
                "datatype": "string",
                "separator": "; ",
                "dc:description": "Other names for this languoid.",
                "required": False,
            },
            {
                "name": "Shorthand",
                "datatype": "string",
                "dc:description": "A handy abbreviation for various purposes",
                "required": True,
            },
            {
                "name": "Dialect_Of",
                "datatype": "string",
                "dc:description": "What language is this languoid a dialect of?",
                "required": False,
            },
            {
                "name": "Alive",
                "datatype": "boolean",
                "dc:description": "Does this languoid have native speakers?",
                "required": True,
            },
            {
                "name": "Proto_Language",
                "datatype": "boolean",
                "dc:description": "Is this languoid a reconstructed proto-language?",
                "required": True,
            },
        )
        args.writer.cldf.add_foreign_key(
            "LanguageTable", "Dialect_Of", "LanguageTable", "ID"
        )
        args.writer.objects["ParameterTable"].append(
            {
                "Name": "Alive",
                "ID": "alive",
                "Description": "Does this languoid have native speakers?",
            }
        )
        args.writer.objects["ParameterTable"].append(
            {
                "Name": "Proto-Language",
                "ID": "proto",
                "Description": "Is this languoid a reconstructed proto-language?",
            }
        )
        args.writer.cldf.add_component(
            {
                "url": "dialects.csv",
                "tableSchema": {
                    "columns": [
                        {
                            "name": "ID",
                            "required": True,
                            "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#id",
                            "datatype": {
                                "base": "string",
                                "format": "[a-zA-Z0-9_\\-]+",
                            },
                        },
                        {
                            "name": "Dialect_ID",
                            "required": True,
                            "datatype": {
                                "base": "string",
                                "format": "[a-zA-Z0-9_\\-]+",
                            },
                        },
                        {
                            "name": "Language_ID",
                            "required": True,
                            "dc:extent": "singlevalued",
                            "dc:description": "The language (as opposed to the dialect)",
                            "datatype": "string",
                        },
                    ]
                },
            }
        )
        args.writer.cldf.add_component("TreeTable")
        args.writer.cldf.add_component("MediaTable")


        args.writer.objects['MediaTable'].append(dict(
                ID="fm-tree-min",
                Media_Type='text/x-nh',
                Download_URL=f"data:text,{min_tree}",
                Path_In_Zip=None
            ))

        args.writer.objects['MediaTable'].append(dict(
                ID="fm-tree",
                Media_Type='text/x-nh',
                Download_URL=f"data:text,{tree}",
                Path_In_Zip=None
            ))

        args.writer.objects['TreeTable'].append(dict(
            ID="fm-tree",
            Name="fm-tree",
            Media_ID="fm-tree",
            Tree_Is_Rooted=True,
            # Tree_Type=type_,
            Description="A relatively conservative tree based on shared innovations.",
            Tree_Branch_Length_Unit=None,
            Source=None,
        ))

        args.writer.objects['TreeTable'].append(dict(
            ID="fm-tree-min",
            Name="fm-tree-min",
            Media_ID="fm-tree-min",
            Tree_Is_Rooted=True,
            # Tree_Type=type_,
            Description="A relatively conservative tree based on shared innovations; dialects are not included.",
            Tree_Branch_Length_Unit=None,
            Source=None,
        ))

        args.writer.cldf.add_foreign_key(
            "LanguageTable", "Dialect_Of", "LanguageTable", "ID"
        )
        args.writer.cldf.add_foreign_key(
            "dialects.csv", "Language_ID", "LanguageTable", "ID"
        )
        args.writer.cldf.add_foreign_key(
            "dialects.csv", "Dialect_ID", "LanguageTable", "ID"
        )
        sources = pybtex.database.parse_file("bib/sources.bib", bib_format="bibtex")
        sources = [Source.from_entry(k, e) for k, e in sources.entries.items()]
        args.writer.cldf.add_sources(*sources)

        bool_dict = {"y": True, "n": False}
        for i, row in lgs.iterrows():
            lg_id = row["ID"]
            # input(row)
            # log.debug(f"""Processing {lg_id}""")
            if row["Glottocode"] and not row["Latitude"]:
                lg = glottolog.languoid(row["Glottocode"])
                if lg.longitude:
                    row["Latitude"] = lg.latitude
                    row["Longitude"] = lg.longitude
                # elif row["Latitude"] != lg.latitude or row["Longitude"] != lg.longitude:
                #     log.warning(f"Coordinate mismatch for {lg}, using glottocoords")
                #     print(row["Latitude"], lg.latitude)
                #     print(row["Longitude"], lg.longitude)
                #     row["Latitude"] = lg.latitude
                #     row["Longitude"] = lg.longitude
                # elif (
                #     row["Latitude"] == lg.latitude and row["Longitude"] == lg.longitude
                # ):
                #     log.debug(f"Matching coords for {lg}")
                #     pass
            alive = bool_dict[row["Alive"]]
            if not alive and not row["Name"].startswith("Proto"):
                row["Name"] = "†" + row["Name"]
            lg_dic = {
                "ID": row["ID"],
                "Name": row["Name"],
                "Shorthand": row["Shorthand"],
                "Alive": alive,
                "Comment": row["Comment"],
                "Proto_Language": (row["ID"][0] == "P"),
            }
            if row["Alternative_Names"]:
                log.info(
                    f"Alternative names for {lg_id}: "
                    + row["Alternative_Names"].replace("; ", ",")
                )
                lg_dic["Alternative_Names"] = row["Alternative_Names"].split("; ")

            if row["Dialect_Of"]:
                args.writer.objects["dialects.csv"].append(
                    {
                        "ID": lg_id + "-" + row["Dialect_Of"],
                        "Dialect_ID": lg_id,
                        "Language_ID": row["Dialect_Of"],
                    }
                )

            args.writer.objects["ValueTable"].append(
                {
                    "ID": lg_id + "_alive",
                    "Language_ID": lg_id,
                    "Parameter_ID": "alive",
                    "Value": bool_dict[row["Alive"]],
                }
            )
            args.writer.objects["ValueTable"].append(
                {
                    "ID": lg_id + "_proto",
                    "Language_ID": lg_id,
                    "Parameter_ID": "proto",
                    "Value": (row["ID"][0] == "P"),
                }
            )

            for opt_col in ["Dialect_Of", "Latitude", "Longitude", "Glottocode"]:
                if row[opt_col]:
                    lg_dic[opt_col] = row[opt_col]

            args.writer.objects["LanguageTable"].append(lg_dic)
