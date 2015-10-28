import click

from regparser import eregs_index
from regparser.commands.dependency_resolver import DependencyResolver
from regparser.notice.build import process_xml


@click.command()
@click.argument('document_number')
def parse_rule_changes(document_number):
    """Parse changes present in a single rule.

    DOCUMENT_NUMBER is the identifier associated with a final rule. If a rule
    has been split, use the split identifiers, a.k.a. version ids."""
    rule_entry = eregs_index.RuleChangesEntry(document_number)
    notice_entry = eregs_index.NoticeEntry(document_number)

    deps = eregs_index.DependencyGraph()
    deps.add(rule_entry, notice_entry)

    deps.validate_for(rule_entry)
    # We don't check for staleness as we want to always execute when given a
    # specific file to process

    # @todo - break apart processing of amendments/changes. We don't need
    # all of the other fields
    notice_xml = notice_entry.read()
    notice = process_xml(notice_xml.to_notice_dict(), notice_xml._xml)
    rule_entry.write(notice)


class RuleChangesResolver(DependencyResolver):
    PATH_PARTS = eregs_index.RuleChangesEntry.PREFIX + (
        '(?P<doc_number>[a-zA-Z0-9-_]+)',)

    def resolution(self):
        args = [self.match.group('doc_number')]
        return parse_rule_changes.main(args, standalone_mode=False)
