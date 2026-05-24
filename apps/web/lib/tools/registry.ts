import type { ToolInfo, ToolKind } from './types';

const sharedPrivacyFaqs = [
  { q: 'When will my uploaded file be deleted?', a: 'Temporary uploads, generated files, and short-lived job records are scheduled for automatic deletion after the configured cleanup window. The default production cleanup window is 60 minutes, and download links remain short-lived.' },
  { q: 'Do I need to create an account?', a: 'You can use basic single-file tools without an account. Accounts are useful for paid limits, saved reports, team access, and future API features.' },
  { q: 'Will the tool read my document content?', a: 'The workflow focuses on metadata and privacy indicators. Reports are designed to show metadata categories, not expose raw document contents.' },
  { q: 'Can I verify the cleaned file?', a: 'Yes. Cleaning tools include a verification step, and you can also upload any supported file to the standalone verification tool.' },
  { q: 'What happens if the file type is not supported?', a: 'Unsupported formats are rejected before processing so you can convert the file to a supported format and try again.' },
  { q: 'Can I choose what to remove?', a: 'After scanning, the interface shows the main detected metadata categories. You can select all items or choose specific items before starting removal.' },
];

const imageAccept = ['.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff', '.heic'];
const pdfAccept = ['.pdf'];
const officeAccept = ['.docx', '.xlsx', '.pptx'];
const videoAccept = ['.mp4', '.mov', '.m4v', '.avi', '.mkv', '.webm'];
const audioAccept = ['.mp3', '.m4a', '.wav', '.flac', '.ogg'];
const zipAccept = ['.zip'];
const c2paAccept = ['.jpg', '.jpeg', '.png', '.webp', '.pdf', '.mp4', '.mov'];
const verifyAccept = [...imageAccept, ...pdfAccept, ...officeAccept, ...videoAccept, ...audioAccept, ...zipAccept];

function tool(input: Omit<ToolInfo, 'apiToolId' | 'endpoint' | 'scanAction'> & Partial<Pick<ToolInfo, 'apiToolId' | 'endpoint' | 'scanAction'>>): ToolInfo {
  const apiToolId = input.apiToolId || input.slug;
  return { ...input, apiToolId, scanAction: input.scanAction || 'scan', endpoint: input.endpoint || `/api/tools/${apiToolId}/${input.defaultAction}` };
}

export const tools: ToolInfo[] = [
  tool({
    slug: 'remove-image-metadata', title: 'Remove Image Metadata Online', shortTitle: 'Remove Image Metadata', defaultAction: 'clean', cleanAction: 'clean', supportsClean: true, kind: 'image', badge: 'Popular', formats: 'JPG, PNG, WebP, TIFF', acceptedFileTypes: imageAccept, action: 'Clean image',
    desc: 'Remove removable EXIF, XMP, IPTC, camera, software, and author metadata from common web images, then verify the result.',
    faq: [
      { q: 'What image metadata can be removed?', a: 'The cleaner targets common metadata groups such as EXIF, XMP, IPTC, camera details, software tags, timestamps, and author fields.' },
      { q: 'Will image quality change?', a: 'The cleaner tries to keep the visual content the same while removing metadata. Some formats may be re-saved depending on file support.' },
      { q: 'Do you support RAW files?', a: 'RAW files are not supported in this version. Export RAW photos to JPG, PNG, WebP, or TIFF before sharing.' },
      { q: 'Can image metadata contain private information?', a: 'Yes. Photos can contain camera model, editing software, timestamps, author fields, thumbnails, and sometimes location data.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'remove-exif-data', title: 'Remove EXIF Data Online', shortTitle: 'Remove EXIF Data', defaultAction: 'clean', cleanAction: 'clean', supportsClean: true, kind: 'image', badge: 'Recommended', formats: 'JPG, PNG, WebP, TIFF', acceptedFileTypes: imageAccept, action: 'Remove EXIF',
    desc: 'Clean camera, device, timestamp, software, and lens details before sharing photos online.',
    faq: [
      { q: 'What is EXIF data?', a: 'EXIF is metadata saved by many cameras and phones. It can include device details, capture settings, dates, and sometimes GPS fields.' },
      { q: 'Does this remove GPS too?', a: 'Yes. GPS fields stored inside removable EXIF metadata are included in the cleaning workflow.' },
      { q: 'Will the photo look different?', a: 'The goal is to keep the photo visually unchanged while removing metadata fields used for identification or tracking.' },
      { q: 'Can EXIF include camera serial numbers?', a: 'Some devices or apps may store detailed camera or software fields. The scan report shows detected metadata categories before removal.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'remove-gps-from-photo', title: 'Remove GPS from Photo', shortTitle: 'Remove GPS from Photo', defaultAction: 'clean', cleanAction: 'clean', supportsClean: true, kind: 'image', badge: 'Location privacy', formats: 'JPG, PNG, WebP, TIFF', acceptedFileTypes: imageAccept, action: 'Remove GPS',
    desc: 'Remove location coordinates from photos while keeping other visual content intact where possible.',
    faq: [
      { q: 'What GPS data can a photo contain?', a: 'Photos may include latitude, longitude, altitude, direction, timestamp, and GPS processing details inside metadata.' },
      { q: 'Does this remove visible location clues?', a: 'No. It removes metadata fields, not visible signs, landmarks, street names, or screenshots inside the picture.' },
      { q: 'Is this different from removing all EXIF?', a: 'Yes. This tool focuses on location-related metadata first. Use the full image metadata tool for broader cleaning.' },
      { q: 'Can social media already remove GPS?', a: 'Some platforms remove location data, but it is safer to clean and verify before uploading or sending a photo.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'remove-pdf-metadata', title: 'Remove PDF Metadata and Hidden Data', shortTitle: 'Remove PDF Metadata', defaultAction: 'clean', cleanAction: 'clean', supportsClean: true, kind: 'pdf', badge: 'Secure', formats: 'PDF', acceptedFileTypes: pdfAccept, action: 'Clean PDF',
    desc: 'Clean PDF document properties, XMP metadata, annotations, embedded files, and active-content indicators where practical, then verify output.',
    faq: [
      { q: 'What PDF metadata can be cleaned?', a: 'The cleaner targets common document properties, XMP packets, producer or software fields, annotations, embedded-file indicators, and active-content indicators where practical.' },
      { q: 'Can PDFs contain hidden files?', a: 'Yes. PDFs may contain attachments, annotations, forms, scripts, thumbnails, and document properties that should be checked before sharing.' },
      { q: 'Will links and forms still work?', a: 'The default cleaner aims to preserve normal PDF readability. More aggressive workflows can affect forms, links, or interactive features.' },
      { q: 'Why do some technical PDF fields appear after cleaning?', a: 'PDF software may add compatibility fields when rebuilding a document. The report separates privacy findings from routine technical fields where possible.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'pdf-privacy-scanner', title: 'PDF Privacy Scanner', shortTitle: 'PDF Privacy Scanner', defaultAction: 'scan', supportsClean: false, kind: 'pdf', badge: 'Scan only', formats: 'PDF', acceptedFileTypes: pdfAccept, action: 'Scan PDF',
    desc: 'Scan PDFs for document info, XMP metadata, attachments, annotations, forms, JavaScript, and privacy-risk indicators.',
    faq: [
      { q: 'Does scan mode change my PDF?', a: 'No. Scan mode inspects the uploaded PDF and returns a privacy report without modifying the file.' },
      { q: 'What does the PDF scanner check?', a: 'It checks common document information, XMP metadata, attachments, forms, annotations, scripts, and other privacy-risk indicators.' },
      { q: 'Can I clean the file after scanning?', a: 'Yes. Use the Remove PDF Metadata tool when you want to clean detected metadata and then verify the output.' },
      { q: 'Why should I scan before sharing?', a: 'A scan helps you understand what a file contains before you send it to a client, employer, colleague, or public website.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'remove-pdf-hidden-data', title: 'Remove PDF Hidden Data', shortTitle: 'Remove PDF Hidden Data', defaultAction: 'clean', cleanAction: 'clean', supportsClean: true, kind: 'pdf', badge: 'Advanced', formats: 'PDF', acceptedFileTypes: pdfAccept, action: 'Clean hidden PDF data',
    desc: 'Use a stronger PDF cleanup mode for metadata, XMP, comments, attachments, forms, JavaScript/action indicators, and hidden-data structures where practical.',
    faq: [
      { q: 'How is this different from Remove PDF Metadata?', a: 'This page uses a stronger hidden-data cleanup mode. It is best for files that may contain comments, attachments, forms, JavaScript, or active-content indicators.' },
      { q: 'Can aggressive cleanup affect the PDF?', a: 'Yes. Removing forms, annotations, actions, or attachments can change interactive behavior. Always verify the cleaned output.' },
      { q: 'What should remain after cleaning?', a: 'Normal PDF structure and technical compatibility data can remain. The report separates technical data from privacy findings.' },
      { q: 'When should I use this tool?', a: 'Use it before external sharing when the PDF was edited, reviewed, exported from business software, or may contain attachments or comments.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'pdf-redaction-checker', title: 'PDF Redaction Checker', shortTitle: 'PDF Redaction Checker', defaultAction: 'scan', supportsClean: false, kind: 'pdf', badge: 'Scan only', formats: 'PDF', acceptedFileTypes: pdfAccept, action: 'Check redactions',
    desc: 'Check whether a PDF may still contain selectable text, unapplied redaction annotations, visual black boxes, or hidden content after redaction.',
    faq: [
      { q: 'What is visual-only redaction?', a: 'Visual-only redaction can happen when black boxes are placed over text but the original text remains selectable underneath.' },
      { q: 'Does the checker modify my PDF?', a: 'No. This is a scan-only report.' },
      { q: 'What should I do if it finds a risk?', a: 'Use a proper redaction workflow, flatten or sanitize the file carefully, and verify again before sharing.' },
      { q: 'Who uses this checker?', a: 'Legal, HR, finance, public-sector, and media teams use it as a quick pre-share risk check.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'remove-docx-metadata', title: 'Remove Office Metadata Before Sharing', shortTitle: 'Remove Office Metadata', defaultAction: 'clean', cleanAction: 'clean', supportsClean: true, kind: 'office', badge: 'Office', formats: 'DOCX, XLSX, PPTX', acceptedFileTypes: officeAccept, action: 'Clean Office file',
    desc: 'Clean core and custom document properties from modern Office files and warn about comments or tracked-change indicators.',
    faq: [
      { q: 'Which Office files are supported?', a: 'This tool supports modern Office formats: DOCX, XLSX, and PPTX.' },
      { q: 'Can it remove author names?', a: 'The cleaner targets common core and custom document properties such as author, company, manager, revision, and software fields.' },
      { q: 'Are old .doc, .xls, and .ppt files supported?', a: 'Legacy binary Office formats are not supported in this version. Save the file as DOCX, XLSX, or PPTX first.' },
      { q: 'Can comments or tracked changes exist?', a: 'Yes. The report can warn about collaboration indicators so you can review the document before sharing.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'docx-hidden-data-scanner', title: 'DOCX Hidden Data Scanner', shortTitle: 'DOCX Hidden Data Scanner', defaultAction: 'scan', supportsClean: false, kind: 'office', badge: 'Word', formats: 'DOCX', acceptedFileTypes: ['.docx'], action: 'Scan DOCX',
    desc: 'Inspect Word documents for comments, tracked changes, author properties, people data, custom XML, and other hidden data before sharing.',
    faq: [
      { q: 'What hidden data can a Word document contain?', a: 'DOCX files can contain author details, document properties, comments, tracked changes, people data, custom XML, and package relationships.' },
      { q: 'Does scan mode change my DOCX?', a: 'No. This tool only inspects the file and reports detected indicators.' },
      { q: 'Can I remove the data after scanning?', a: 'Use the Remove Office Metadata tool when you want to clean a supported Office file.' },
      { q: 'Are legacy .doc files supported?', a: 'No. Save legacy documents as DOCX before using this scanner.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'xlsx-hidden-data-scanner', title: 'Excel Hidden Data Scanner', shortTitle: 'Excel Hidden Data Scanner', defaultAction: 'scan', supportsClean: false, kind: 'office', badge: 'Excel', formats: 'XLSX', acceptedFileTypes: ['.xlsx'], action: 'Scan Excel',
    desc: 'Scan Excel workbooks for hidden sheets, external links, workbook properties, comments, custom XML, and privacy-risk workbook data.',
    faq: [
      { q: 'What Excel hidden data can be risky?', a: 'Hidden sheets, external links, workbook names, formulas, comments, author properties, and custom XML can reveal business context.' },
      { q: 'Does this remove hidden sheets?', a: 'This page is scan-only. Cleaning hidden sheets or formulas can affect workbook logic, so the first release reports the risk clearly.' },
      { q: 'Can formulas leak data sources?', a: 'Yes. Formulas and external links can reference internal paths, server names, or source files.' },
      { q: 'Are .xls files supported?', a: 'No. Convert legacy .xls files to XLSX before scanning.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'pptx-remove-notes-hidden-slides', title: 'Remove Speaker Notes and Hidden Slides', shortTitle: 'Remove PPTX Notes', defaultAction: 'clean', cleanAction: 'clean', supportsClean: true, kind: 'office', badge: 'PowerPoint', formats: 'PPTX', acceptedFileTypes: ['.pptx'], action: 'Clean presentation',
    desc: 'Scan and clean PowerPoint speaker notes, comments, hidden slide indicators, properties, and collaboration metadata before sending presentations.',
    faq: [
      { q: 'Can PowerPoint notes be private?', a: 'Yes. Speaker notes and comments often contain draft text, client notes, sales talking points, or internal context.' },
      { q: 'Will this change my slides?', a: 'It removes hidden/collaboration data where practical, but visible slide content should remain.' },
      { q: 'Can hidden slides leak information?', a: 'Yes. Hidden slides may remain inside the PPTX package even if they do not appear during presenting.' },
      { q: 'Should I verify after cleaning?', a: 'Yes. The tool re-scans the cleaned presentation so you can confirm no removable private metadata is detected.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'remove-video-metadata', title: 'Remove Video Metadata Online', shortTitle: 'Remove Video Metadata', defaultAction: 'clean', cleanAction: 'clean', supportsClean: true, kind: 'media', badge: 'New', formats: 'MP4, MOV, M4V, AVI, MKV, WebM', acceptedFileTypes: videoAccept, action: 'Clean video',
    desc: 'Scan and remove hidden creator, location, software, comments, and container metadata from videos, then verify the cleaned file.',
    faq: [
      { q: 'What video metadata can be removed?', a: 'The cleaner targets common container and stream tags such as title, author, location, creation time, software, and comments while keeping playable technical data.' },
      { q: 'Will video quality change?', a: 'The workflow tries to remux/copy streams where possible to avoid quality loss. Some formats may require a different cleanup path.' },
      { q: 'Can videos contain location metadata?', a: 'Yes. Some phones and apps may store GPS or location-style metadata in video containers.' },
      { q: 'Why can technical video data remain?', a: 'Codec, duration, stream, and container fields are needed for playback and are shown separately from private metadata.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'remove-audio-metadata', title: 'Remove Audio Metadata Online', shortTitle: 'Remove Audio Metadata', defaultAction: 'clean', cleanAction: 'clean', supportsClean: true, kind: 'media', badge: 'New', formats: 'MP3, M4A, WAV, FLAC, OGG', acceptedFileTypes: audioAccept, action: 'Clean audio',
    desc: 'Remove artist, album, title, comments, copyright, and other user metadata from audio files before publishing or sending.',
    faq: [
      { q: 'What audio metadata can be removed?', a: 'Audio files may contain ID3 tags, artist and album fields, title, comments, encoder data, cover art, and copyright notes.' },
      { q: 'Will audio quality change?', a: 'The cleaner aims to remove metadata without changing the audio stream when the format allows it.' },
      { q: 'Can podcast files contain private metadata?', a: 'Yes. Audio exports can include names, software, project notes, dates, or cover-art metadata.' },
      { q: 'Can cover art remain?', a: 'Some cover art can be treated as embedded content. The report highlights removable categories where supported.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'zip-privacy-scanner', title: 'ZIP Privacy Scanner', shortTitle: 'ZIP Privacy Scanner', defaultAction: 'scan', supportsClean: false, kind: 'archive', badge: 'Scan only', formats: 'ZIP', acceptedFileTypes: zipAccept, action: 'Scan ZIP',
    desc: 'Scan ZIP files for risky filenames, system metadata artifacts, nested archives, unsafe paths, and metadata-bearing files before sharing.',
    faq: [
      { q: 'Does this unzip my files publicly?', a: 'No. The scanner inspects the archive structure inside the private processing job and returns a report.' },
      { q: 'What ZIP risks can it find?', a: 'It can detect risky paths, macOS metadata artifacts, system files, nested archives, and file types that may contain their own metadata.' },
      { q: 'Does it clean ZIP files?', a: 'Use Clean ZIP Privacy Risks when you want to remove unsafe paths, system metadata artifacts, and sensitive-looking config files.' },
      { q: 'Can a ZIP contain hidden metadata?', a: 'Yes. The archive itself can reveal filenames and folder paths, and the files inside can contain their own metadata.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'remove-zip-privacy-risks', title: 'Remove ZIP Privacy Risks', shortTitle: 'Clean ZIP Privacy Risks', defaultAction: 'clean', cleanAction: 'clean', supportsClean: true, kind: 'archive', badge: 'Cleaner', formats: 'ZIP', acceptedFileTypes: zipAccept, action: 'Clean ZIP',
    desc: 'Remove unsafe paths, system metadata artifacts, and sensitive-looking config files from ZIP archives, then verify the cleaned archive.',
    faq: [
      { q: 'What does ZIP cleaning remove?', a: 'The cleaner removes unsafe paths, macOS/Windows system metadata artifacts, and sensitive-looking config filenames such as .env or password files where detected.' },
      { q: 'Does it remove all files inside the ZIP?', a: 'No. It does not delete normal documents, photos, videos, or nested archives by default. Those files should be scanned with their matching privacy tools.' },
      { q: 'Can ZIP cleaning change the archive?', a: 'Yes. It creates a new cleaned ZIP without selected risky entries. Always verify the cleaned archive before sending it.' },
      { q: 'Why can metadata-bearing files still remain?', a: 'A ZIP can contain PDF, Office, image, audio, or video files that have their own metadata. Clean those files separately before adding them back to an archive.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'verify-file-metadata', title: 'Verify File Metadata Removal', shortTitle: 'Verify Cleaned File', defaultAction: 'verify', scanAction: 'verify', supportsClean: false, kind: 'verify', badge: 'Verification', formats: 'JPG, PNG, WebP, PDF, DOCX, XLSX, PPTX, MP4, MP3, ZIP', acceptedFileTypes: verifyAccept, action: 'Verify file',
    desc: 'Re-scan a cleaned file and see whether removable private metadata is still detected by current scanners.',
    faq: [
      { q: 'What does verification mean?', a: 'Verification re-runs the relevant scanner family and reports remaining findings, warnings, and metadata categories.' },
      { q: 'Does verification change the file?', a: 'No. Verification is a scan-only workflow. It reads supported metadata indicators and shows a report.' },
      { q: 'When should I use verification?', a: 'Use it after cleaning a file, after exporting a file from another app, or before sharing sensitive documents externally.' },
      { q: 'Can I verify files cleaned somewhere else?', a: 'Yes. Upload a supported file and the verifier will scan it with the available scanner for that file type.' },
      ...sharedPrivacyFaqs,
    ],
  }),
  tool({
    slug: 'detect-content-credentials', title: 'Detect Content Credentials', shortTitle: 'Detect C2PA Credentials', defaultAction: 'scan', supportsClean: false, kind: 'ai', badge: 'C2PA', formats: 'JPG, PNG, WebP, PDF, MP4, MOV', acceptedFileTypes: c2paAccept, action: 'Detect credentials',
    desc: 'Use the official c2patool runtime to detect C2PA / Content Credentials manifest data in supported media files.',
    faq: [
      { q: 'What are Content Credentials?', a: 'Content Credentials are provenance records that can describe how a file was created, edited, or signed by compatible tools.' },
      { q: 'Does no C2PA mean a file is human-made?', a: 'No. Missing C2PA only means this scanner did not find a supported manifest. It is not a guarantee of human origin.' },
      { q: 'Does this tool remove C2PA?', a: 'No. This page is scan-only. Use metadata cleaning tools if you want to remove removable provenance metadata where supported.' },
      { q: 'Which files can contain C2PA?', a: 'C2PA can appear in supported image, video, and document formats depending on the creator app and export settings.' },
      ...sharedPrivacyFaqs,
    ],
  }),
];

export const kindLabels: Record<ToolKind, string> = { image: 'Image Privacy', pdf: 'PDF Privacy', office: 'Office Privacy', media: 'Media Privacy', archive: 'Archive Privacy', verify: 'Verification', ai: 'AI Provenance' };

export function getTool(slug: string) {
  const item = tools.find((t) => t.slug === slug);
  if (!item) throw new Error(`Unknown tool: ${slug}`);
  return item;
}
