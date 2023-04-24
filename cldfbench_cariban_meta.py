import pathlib
import pandas as pd
from cldfbench import Dataset as BaseDataset
import pybtex
from pycldf.sources import Source


import logging
import colorlog

log = logging.getLogger(__name__)
log.propagate = True
log.setLevel(logging.INFO)
handler = colorlog.StreamHandler(None)
handler.setFormatter(
    colorlog.ColoredFormatter("%(log_color)s%(levelname)-7s%(reset)s %(message)s")
)
log.addHandler(handler)


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "cariban_meta"

    def get_lg(self, lg_id):
        lgs = pd.read_csv(self.cldf_dir/"languages.csv", keep_default_na=False)
        return lgs[lgs["ID"] == lg_id].to_dict("records")[0]

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
                "url": "DialectTable",
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
        args.writer.cldf.add_foreign_key(
            "LanguageTable", "Dialect_Of", "LanguageTable", "ID"
        )
        args.writer.cldf.add_foreign_key(
            "DialectTable", "Language_ID", "LanguageTable", "ID"
        )
        args.writer.cldf.add_foreign_key(
            "DialectTable", "Dialect_ID", "LanguageTable", "ID"
        )
        sources = pybtex.database.parse_file("etc/sources.bib", bib_format="bibtex")
        sources = [Source.from_entry(k, e) for k, e in sources.entries.items()]
        args.writer.cldf.add_sources(*sources)


        lgs = pd.read_csv(
            "raw/cariban_language_list.csv",
            dtype={"Latitude": "float", "Longitude": "float"},
        )
        bool_dict = {"y": True, "n": False}
        for i, row in lgs.iterrows():
            lg_id = row["ID"]
            log.debug(f"""Processing {lg_id}""")
            if not pd.isnull(row["Glottocode"]):
                lg = glottolog.languoid(row["Glottocode"])
                if not lg.longitude:
                    log.debug(f"No glottocoords for {lg}, using own")
                elif row["Latitude"] != lg.latitude or row["Longitude"] != lg.longitude:
                    log.warning(f"Coordinate mismatch for {lg}, using glottocode")
                    print(row["Latitude"], lg.latitude)
                    print(row["Longitude"], lg.longitude)
                    row["Latitude"] = lg.latitude
                    row["Longitude"] = lg.longitude
                elif (
                    row["Latitude"] == lg.latitude and row["Longitude"] == lg.longitude
                ):
                    log.debug(f"Matching coords for {lg}")
                    pass
            lg_dic = {
                "ID": row["ID"],
                "Name": row["Name"],
                "Shorthand": row["Shorthand"],
                "Alive": bool_dict[row["Alive"]],
                "Comment": row["Comment"],
                "Proto_Language": (row["ID"][0] == "P"),
            }
            if not pd.isnull(row["Alternative_Names"]):
                log.info(
                    f"Alternative names for {lg_id}: "
                    + row["Alternative_Names"].replace("; ", ",")
                )
                lg_dic["Alternative_Names"] = row["Alternative_Names"].split("; ")

            if not pd.isnull(row["Dialect_Of"]):
                args.writer.objects["DialectTable"].append(
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
                if not pd.isnull(row[opt_col]):
                    lg_dic[opt_col] = row[opt_col]

            args.writer.objects["LanguageTable"].append(lg_dic)
